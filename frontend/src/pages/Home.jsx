import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';

export default function Home() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/posts/')
      .then(res => {
        setPosts(res.data.results || res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="container" style={{ textAlign: 'center' }}>Загрузка...</div>;

  return (
    <div className="container">
      <h1 style={{ fontSize: '2rem', marginBottom: '1.5rem' }}>📽️ Свежие посты</h1>
      {posts.length === 0 && <p>Постов пока нет</p>}
      {posts.map(post => (
        <div key={post.id} className="post-card" onClick={() => navigate(`/post/${post.id}`)}>
          {post.image && <img src={post.image} alt={post.title} className="post-image" style={{ maxHeight: '250px' }} />}
          <h2 className="post-title">{post.title}</h2>
          <div className="post-meta">
            <span>✍️ {post.author?.username}</span>
            <span>📅 {new Date(post.created_at).toLocaleDateString()}</span>
            <span>👁️ {post.views}</span>
            <span>❤️ {post.favorites_count}</span>
          </div>
          <div className="post-excerpt">{post.text?.substring(0, 200)}...</div>
          <button className="read-more">Читать дальше →</button>
        </div>
      ))}
    </div>
  );
}