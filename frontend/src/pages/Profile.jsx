import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export default function Profile() {
  const { user, updateUser } = useAuth();
  const [form, setForm] = useState({ username: user?.username || '', email: user?.email || '', bio: user?.bio || '' });
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await updateUser(form);
      setMessage('Обновлено!');
      setTimeout(() => setMessage(''), 3000);
    } catch {
      setMessage('Ошибка');
    }
  };

  if (!user) return <div className="container">Загрузка...</div>;

  return (
    <div className="container">
      <div className="auth-form">
        <h2>Мой профиль</h2>
        {message && <p style={{ color: '#a5f0a5', textAlign: 'center' }}>{message}</p>}
        <form onSubmit={handleSubmit}>
          <input type="text" placeholder="Логин" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required />
          <input type="email" placeholder="Email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required />
          <textarea rows="3" placeholder="О себе" value={form.bio} onChange={e => setForm({ ...form, bio: e.target.value })} />
          <button type="submit">Сохранить</button>
        </form>
      </div>
    </div>
  );
}