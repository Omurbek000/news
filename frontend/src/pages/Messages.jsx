import { useEffect, useRef, useState } from 'react';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

export default function Messages() {
  const { user, refreshUnreadCount } = useAuth();
  const [dialogs, setDialogs] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const chatRef = useRef(null);

  const loadDialogs = () => api.get('/messages/dialogs/').then(res => {
    setDialogs(res.data.results || res.data);
  });

  useEffect(() => {
    if (!user) return;
    api.get('/messages/dialogs/').then(res => {
      setDialogs(res.data.results || res.data);
    });
  }, [user]);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages]);

  const loadDialog = async (userId) => {
    const dialogUser = dialogs.find(d => d.user_id === userId);
    if (dialogUser) setSelectedUser(dialogUser);
    const res = await api.get(`/messages/dialog/${userId}/`);
    setMessages(res.data.results || res.data);
    await api.post(`/messages/dialog/${userId}/read/`);
    await loadDialogs();
    refreshUnreadCount();
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!text.trim() || !selectedUser) return;
    await api.post('/messages/', { recipient: selectedUser.user_id, text });
    setText('');
    await loadDialog(selectedUser.user_id);
  };

  if (!user) return <div className="container">Требуется вход</div>;

  return (
    <div className="container">
      <h1 style={{ fontSize: '2rem', marginBottom: '1.5rem' }}>💬 Сообщения</h1>
      <div className="messages-container">
        <div className="dialogs-list">
          <h3>Диалоги</h3>
          {dialogs.length === 0 && <p>Нет диалогов</p>}
          {dialogs.map(d => (
            <div key={d.user_id} onClick={() => loadDialog(d.user_id)} style={{
              padding: '0.6rem',
              marginBottom: '0.5rem',
              borderRadius: '40px',
              background: selectedUser?.user_id === d.user_id ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.05)',
              cursor: 'pointer'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                <strong>{d.username}</strong>
                {d.unread_count > 0 && <span className="badge">{d.unread_count}</span>}
              </div>
              {d.last_message && (
                <div style={{
                  fontSize: '0.8rem',
                  opacity: 0.7,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap'
                }}>{d.last_message}</div>
              )}
            </div>
          ))}
        </div>
        <div className="chat-area">
          {selectedUser ? (
            <>
              <h3>Чат с {selectedUser.username}</h3>
              <div ref={chatRef} style={{ maxHeight: '400px', overflowY: 'auto', marginBottom: '1rem' }}>
                {messages.map(m => (
                  <div key={m.id} style={{ textAlign: m.sender_username === user.username ? 'right' : 'left', marginBottom: '0.7rem' }}>
                    <div style={{
                      display: 'inline-block',
                      background: m.sender_username === user.username ? '#6d28d9' : 'rgba(255,255,255,0.2)',
                      padding: '0.5rem 1rem',
                      borderRadius: '20px',
                      maxWidth: '80%'
                    }}>
                      <strong>{m.sender_username}:</strong> {m.text}
                    </div>
                  </div>
                ))}
              </div>
              <form onSubmit={sendMessage} style={{ display: 'flex', gap: '0.5rem' }}>
                <input type="text" value={text} onChange={e => setText(e.target.value)} placeholder="Сообщение..." style={{ flex: 1, padding: '0.7rem', borderRadius: '40px', border: 'none', background: 'rgba(255,255,255,0.1)', color: 'white' }} />
                <button type="submit" style={{ background: '#7c3aed', border: 'none', borderRadius: '40px', padding: '0 1.2rem', color: 'white', cursor: 'pointer' }}>→</button>
              </form>
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: '2rem' }}>Выберите диалог</div>
          )}
        </div>
      </div>
    </div>
  );
}
