import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

export default function Settings() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newPassword2, setNewPassword2] = useState('');
  const [pwMessage, setPwMessage] = useState('');
  const [pwError, setPwError] = useState('');

  const [confirmDelete, setConfirmDelete] = useState(false);
  const [delError, setDelError] = useState('');

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPwMessage('');
    setPwError('');
    if (newPassword !== newPassword2) {
      setPwError('Пароли не совпадают');
      return;
    }
    try {
      await api.put('/auth/change-password/', {
        old_password: oldPassword,
        new_password: newPassword,
        new_password2: newPassword2,
      });
      setPwMessage('Пароль успешно изменён!');
      setOldPassword('');
      setNewPassword('');
      setNewPassword2('');
    } catch (err) {
      setPwError(err.response?.data?.detail || err.response?.data?.old_password?.[0] || 'Ошибка смены пароля');
    }
  };

  const handleDeleteAccount = async () => {
    setDelError('');
    try {
      await api.delete('/users/me/');
      logout();
      navigate('/');
    } catch (err) {
      setDelError(err.response?.data?.detail || 'Не удалось удалить аккаунт');
    }
  };

  if (!user) return <div className="container">Требуется вход</div>;

  return (
    <div className="container">
      <div className="auth-form" style={{ maxWidth: '500px' }}>
        <h2>Настройки</h2>

        {/* Смена пароля */}
        <h3 style={{ color: '#f97316', marginBottom: '1rem', fontSize: '1.1rem' }}>Смена пароля</h3>
        {pwMessage && <p className="success-message">{pwMessage}</p>}
        {pwError && <p className="error-message">{pwError}</p>}
        <form onSubmit={handleChangePassword}>
          <input
            type="password"
            placeholder="Текущий пароль"
            value={oldPassword}
            onChange={e => setOldPassword(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Новый пароль"
            value={newPassword}
            onChange={e => setNewPassword(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Повторите новый пароль"
            value={newPassword2}
            onChange={e => setNewPassword2(e.target.value)}
            required
          />
          <button type="submit">Изменить пароль</button>
        </form>

        <hr style={{ border: 'none', borderTop: '1px solid #334155', margin: '2rem 0' }} />

        {/* Удаление аккаунта */}
        <h3 style={{ color: '#ef4444', marginBottom: '1rem', fontSize: '1.1rem' }}>Удаление аккаунта</h3>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1rem' }}>
          Это действие необратимо. Все ваши посты, комментарии и сообщения будут удалены.
        </p>
        {delError && <p className="error-message">{delError}</p>}
        {!confirmDelete ? (
          <button
            onClick={() => setConfirmDelete(true)}
            style={{
              width: '100%', padding: '0.8rem', borderRadius: '40px', border: '2px solid #ef4444',
              background: 'transparent', color: '#ef4444', fontWeight: '600', cursor: 'pointer',
              fontSize: '1rem', transition: '0.2s',
            }}
          >
            Удалить аккаунт
          </button>
        ) : (
          <div style={{ textAlign: 'center' }}>
            <p style={{ color: '#ef4444', marginBottom: '1rem', fontWeight: '600' }}>
              Вы уверены?
            </p>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <button
                onClick={handleDeleteAccount}
                style={{
                  flex: 1, padding: '0.8rem', borderRadius: '40px', border: 'none',
                  background: '#ef4444', color: 'white', fontWeight: '600', cursor: 'pointer',
                  fontSize: '1rem',
                }}
              >
                Да, удалить
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                style={{
                  flex: 1, padding: '0.8rem', borderRadius: '40px', border: '1px solid #334155',
                  background: 'transparent', color: '#94a3b8', fontWeight: '600', cursor: 'pointer',
                  fontSize: '1rem',
                }}
              >
                Отмена
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
