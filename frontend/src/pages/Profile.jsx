import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Avatar from 'react-avatar';

export default function Profile() {
  const { user, updateUser, uploadAvatar } = useAuth();
  const [form, setForm] = useState({
    username: user?.username || '',
    email: user?.email || '',
    phone: user?.phone || '',
    age: user?.age || '',
    bio: user?.bio || '',
  });
  const [avatarFile, setAvatarFile] = useState(null);
  const [avatarPreview, setAvatarPreview] = useState(user?.avatar || null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await updateUser(form);
      setMessage('Профиль обновлён!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError('Ошибка обновления');
      setTimeout(() => setError(''), 3000);
    }
  };

  const handleAvatarChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setAvatarFile(file);
    setAvatarPreview(URL.createObjectURL(file));
    try {
      await uploadAvatar(file);
      setMessage('Аватар обновлён!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError('Ошибка загрузки аватара');
      setTimeout(() => setError(''), 3000);
    }
  };

  if (!user) return <div className="container loading">Загрузка...</div>;

  return (
    <div className="container">
      <div className="auth-form">
        <h2>Мой профиль</h2>

        {message && <p className="success-message">{message}</p>}
        {error && <p className="error-message">{error}</p>}

        <div className="avatar-section">
          {avatarPreview ? (
            <img src={avatarPreview} alt="Avatar" className="profile-avatar" />
          ) : (
            <Avatar name={user.username} size="80" round="80px" />
          )}
          <label className="avatar-label">
            📷 Загрузить фото
            <input type="file" accept="image/*" onChange={handleAvatarChange} hidden />
          </label>
        </div>

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Логин"
            value={form.username}
            onChange={e => setForm({ ...form, username: e.target.value })}
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={e => setForm({ ...form, email: e.target.value })}
            required
          />
          <input
            type="tel"
            placeholder="Телефон"
            value={form.phone}
            onChange={e => setForm({ ...form, phone: e.target.value })}
          />
          <input
            type="number"
            placeholder="Возраст"
            value={form.age}
            onChange={e => setForm({ ...form, age: e.target.value ? Number(e.target.value) : '' })}
            min="17"
            max="100"
          />
          <textarea
            rows="3"
            placeholder="О себе"
            value={form.bio}
            onChange={e => setForm({ ...form, bio: e.target.value })}
          />
          <button type="submit">Сохранить изменения</button>
        </form>
      </div>
    </div>
  );
}