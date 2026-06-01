import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { useAuth } from '../contexts/AuthContext';

export default function CreatePost() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [category, setCategory] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/categories/')
      .then(res => setCategories(res.data.results || res.data))
      .catch(err => console.error(err));
  }, []);

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !text.trim()) {
      setError('Заголовок и текст обязательны');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('text', text);
      formData.append('status', 'published');
      if (category) formData.append('category', category);
      if (imageFile) formData.append('image', imageFile);
      await api.post('/posts/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка при создании поста');
    } finally {
      setLoading(false);
    }
  };

  if (!user) return <div className="container">Требуется авторизация</div>;

  return (
    <div className="container">
      <div className="auth-form" style={{ maxWidth: '700px' }}>
        <h2>✍️ Новый пост</h2>
        {error && <p className="error-message">{error}</p>}
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Заголовок"
            value={title}
            onChange={e => setTitle(e.target.value)}
            required
          />
          <textarea
            rows="6"
            placeholder="Текст поста..."
            value={text}
            onChange={e => setText(e.target.value)}
            required
          />
          <select value={category} onChange={e => setCategory(e.target.value)}>
            <option value="">Без категории</option>
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>
          <div className="image-upload">
            <label className="image-label">
              📷 Прикрепить изображение
              <input type="file" accept="image/*" onChange={handleImageChange} hidden />
            </label>
            {imagePreview && (
              <div className="image-preview">
                <img src={imagePreview} alt="Превью" />
                <button type="button" onClick={() => { setImageFile(null); setImagePreview(''); }}>✖</button>
              </div>
            )}
          </div>
          <button type="submit" disabled={loading}>
            {loading ? 'Публикация...' : 'Опубликовать'}
          </button>
        </form>
      </div>
    </div>
  );
}