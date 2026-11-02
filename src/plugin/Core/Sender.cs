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
                // Companion nic nie odsyła: gotowość do odczytu bez danych oznacza zamknięte połączenie.
                if (_socket.Poll(0, SelectMode.SelectRead) && _socket.Available == 0) { Close(); return "disconnected"; }
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

        private void Close()
        {
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
