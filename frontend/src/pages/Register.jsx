import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Register() {
  const [form, setForm] = useState({ username: '', email: '', password: '', password2: '' });
  const [error, setError] = useState('');
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.password2) {
      setError('Пароли не совпадают');
      return;
    }
    try {
      await register(form);
      navigate('/login');
    } catch {
      setError('Ошибка регистрации');
    }
  };

  return (
    <div className="container">
      <div className="auth-form">
        <h2>Регистрация</h2>
        {error && <p style={{ color: '#ffa5a5', textAlign: 'center' }}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <input name="username" placeholder="Логин" value={form.username} onChange={handleChange} required />
          <input name="email" type="email" placeholder="Email" value={form.email} onChange={handleChange} required />
          <input name="password" type="password" placeholder="Пароль" value={form.password} onChange={handleChange} required />
          <input name="password2" type="password" placeholder="Повторите пароль" value={form.password2} onChange={handleChange} required />
          <button type="submit">Зарегистрироваться</button>
        </form>
        <div className="link">Уже есть аккаунт? <Link to="/login">Войти</Link></div>
      </div>
    </div>
  );
}