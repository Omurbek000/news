import { useEffect, useState } from 'react';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

export default function Messages() {
  const { user } = useAuth();
  const [dialogs, setDialogs] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');

  useEffect(() => {
    if (user) {
      api.get('/messages/').then(res => {
        const msgs = res.data.results || res.data;
        const users = new Set();
        msgs.forEach(m => {
          if (m.sender_username !== user.username) users.add(m.sender_username);
          if (m.recipient_username !== user.username) users.add(m.recipient_username);
        });
        setDialogs(Array.from(users));
      });
    }
  }, [user]);

  const loadDialog = async (username) => {
    setSelectedUser(username);
    const res = await api.get('/messages/');
    const all = res.data.results || res.data;
    const filtered = all.filter(m =>
      (m.sender_username === username && m.recipient_username === user.username) ||
      (m.sender_username === user.username && m.recipient_username === username)
    );
    setMessages(filtered);
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!text.trim() || !selectedUser) return;
    await api.post('/messages/', { recipient: selectedUser, text });
    setText('');
    loadDialog(selectedUser);
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
            <div key={d} onClick={() => loadDialog(d)} style={{
              padding: '0.6rem',
              marginBottom: '0.5rem',
              borderRadius: '40px',
              background: selectedUser === d ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.05)',
              cursor: 'pointer'
            }}>{d}</div>
          ))}
        </div>
        <div className="chat-area">
          {selectedUser ? (
            <>
              <h3>Чат с {selectedUser}</h3>
              <div style={{ maxHeight: '400px', overflowY: 'auto', marginBottom: '1rem' }}>
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