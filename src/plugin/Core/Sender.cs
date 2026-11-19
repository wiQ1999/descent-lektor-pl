using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Text;

namespace LektorPL.Core
{
    /// <summary>
    /// Wysyła linie dziennika do companiona przez TCP na localhost (JSON lines).
    ///
    /// Bez wątków i operacji blokujących: gniazdo jest nieblokujące, a połączenie i wysyłka idą w LateUpdate.
    /// Plugin nie dokłada więc nic, co musiałoby się zakończyć przy wyjściu z gry (D40). Bez połączenia
    /// zdarzenia przepadają, bo companion po starcie czyta tylko nowe okna. Połączenie jest ponawiane.
    /// Companion odsyła stan dla nakładki (linie JSON): odczyt też jest nieblokujący, każda pełna linia trafia do OnLine.
    /// </summary>
    internal sealed class Sender : IDisposable
    {
        private const int MaxQueue = 512;
        private const float RetrySeconds = 2f;
        private const float ConnectTimeout = 2f;

        private readonly IPEndPoint _endpoint;
        private readonly Queue<byte[]> _queue = new Queue<byte[]>();
        private Socket _socket;
        private bool _connecting;
        private float _connectStarted, _nextAttempt;
        private byte[] _current;
        private int _offset;
        private const int MaxLine = 1 << 20;
        private readonly byte[] _readBuf = new byte[16384];
        private readonly List<byte> _line = new List<byte>(4096);

        /// <summary>Pełna linia od companiona (bez znaku nowej linii).</summary>
        public Action<string> OnLine;

        public Sender(int port)
        {
            _endpoint = new IPEndPoint(IPAddress.Loopback, port);
        }

        public bool Connected => _socket != null && !_connecting;

        /// <summary>Wywoływane z <see cref="EventLog"/> dla każdej zapisanej linii.</summary>
        public void Enqueue(string line)
        {
            if (!Connected || _queue.Count >= MaxQueue) return;
            _queue.Enqueue(Encoding.UTF8.GetBytes(line + "\n"));
        }

        /// <summary>Zwraca opis zmiany stanu połączenia (do dziennika) albo null.</summary>
        public string Pump(float now)
        {
            if (_socket == null)
                return now >= _nextAttempt ? BeginConnect(now) : null;
            if (_connecting)
                return CheckConnect(now);
            return Send();
        }

        private string BeginConnect(float now)
        {
            _nextAttempt = now + RetrySeconds;
            try
            {
                _socket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp) { Blocking = false, NoDelay = true };
                _connecting = true;
                _connectStarted = now;
                try { _socket.Connect(_endpoint); _connecting = false; return "connected"; }
                catch (SocketException e) when (e.SocketErrorCode == SocketError.WouldBlock || e.SocketErrorCode == SocketError.InProgress) { }
            }
            catch (Exception) { Close(); }
            return null;
        }

        private string CheckConnect(float now)
        {
            try
            {
                if (_socket.Poll(0, SelectMode.SelectWrite)) { _connecting = false; return "connected"; }
                if (_socket.Poll(0, SelectMode.SelectError) || now - _connectStarted > ConnectTimeout) Close();
            }
            catch (Exception) { Close(); }
            return null;
        }

        private string Send()
        {
            try
            {
                // Gotowość do odczytu bez danych oznacza zamknięte połączenie; dane to stan od companiona.
                if (_socket.Poll(0, SelectMode.SelectRead))
                {
                    if (_socket.Available == 0) { Close(); return "disconnected"; }
                    if (!Receive()) { Close(); return "disconnected"; }
                }
                while (_current != null || _queue.Count > 0)
                {
                    if (_current == null) { _current = _queue.Dequeue(); _offset = 0; }
                    int n = _socket.Send(_current, _offset, _current.Length - _offset, SocketFlags.None, out SocketError err);
                    if (err == SocketError.WouldBlock) break;
                    if (err != SocketError.Success) { Close(); return "disconnected"; }
                    _offset += n;
                    if (_offset >= _current.Length) _current = null;
                }
            }
            catch (Exception) { Close(); return "disconnected"; }
            return null;
        }

        private bool Receive()
        {
            while (_socket.Available > 0)
            {
                int n = _socket.Receive(_readBuf, 0, _readBuf.Length, SocketFlags.None, out SocketError err);
                if (err == SocketError.WouldBlock) return true;
                if (err != SocketError.Success || n <= 0) return false;
                for (int i = 0; i < n; i++)
                {
                    byte b = _readBuf[i];
                    if (b != (byte)'\n') { if (_line.Count < MaxLine) _line.Add(b); continue; }
                    string line = Encoding.UTF8.GetString(_line.ToArray());
                    _line.Clear();
                    try { OnLine?.Invoke(line); } catch (Exception) { }
                }
            }
            return true;
        }

        private void Close()
        {
            _line.Clear();
            try { _socket?.Close(); } catch (Exception) { }
            _socket = null;
            _connecting = false;
            _current = null;
            _queue.Clear();
        }

        public void Dispose()
        {
            Close();
        }
    }
}
