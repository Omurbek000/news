import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../api/axios';

export default function Home() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [nextPageUrl, setNextPageUrl] = useState(null);
  const [prevPageUrl, setPrevPageUrl] = useState(null);
  const [categories, setCategories] = useState([]);
  const [searchParams, setSearchParams] = useSearchParams();

  const searchQuery = searchParams.get('search') || '';
  const categoryId = searchParams.get('category') || '';
  const ordering = searchParams.get('ordering') || '-created_at';

  const fetchPosts = async (url = null) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      if (categoryId) params.append('category', categoryId);
      if (ordering) params.append('ordering', ordering);
      const finalUrl = url || `/posts/?${params.toString()}`;
      const res = await api.get(finalUrl);
      setPosts(res.data.results || res.data);
      setNextPageUrl(res.data.next);
      setPrevPageUrl(res.data.previous);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, [searchQuery, categoryId, ordering]);

  useEffect(() => {
    api.get('/categories/')
      .then(res => setCategories(res.data.results || res.data))
      .catch(console.error);
  }, []);

  const handlePrev = () => {
    if (prevPageUrl) fetchPosts(prevPageUrl);
  };

  const handleNext = () => {
    if (nextPageUrl) fetchPosts(nextPageUrl);
  };

  const handleCategoryChange = (e) => {
    const val = e.target.value;
    const newParams = { ...Object.fromEntries(searchParams) };
    if (val) newParams.category = val;
    else delete newParams.category;
    setSearchParams(newParams);
  };

  const handleOrderingChange = (e) => {
    setSearchParams({ ...Object.fromEntries(searchParams), ordering: e.target.value });
  };

  if (loading && posts.length === 0) return <div className="loading">Загрузка...</div>;

  return (
    <div className="container home-container">
      <div className="filters-bar">
        <div className="filter-group">
          <label>Категория:</label>
          <select value={categoryId} onChange={handleCategoryChange}>
            <option value="">Все</option>
            {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="filter-group">
          <label>Сортировка:</label>
          <select value={ordering} onChange={handleOrderingChange}>
            <option value="-created_at">Новые сначала</option>
            <option value="created_at">Старые сначала</option>
            <option value="-views">Самые просматриваемые</option>
            <option value="-favorites_count">Самые популярные</option>
          </select>
        </div>
      </div>

      {posts.length === 0 && !loading && <div className="no-posts">Постов не найдено</div>}

      <div className="posts-list">
        {posts.map(post => (
          <div key={post.id} className="post-card">
            {post.image && (
              <img
                src={post.image.startsWith('http') ? post.image : `http://127.0.0.1:8080${post.image}`}
                alt={post.title}
                className="post-image"
              />
            )}
            <div className="post-content">
              <h2 className="post-title"><Link to={`/post/${post.id}`}>{post.title}</Link></h2>
              <div className="post-meta">
                <span>{post.author?.username}</span>
                <span>{new Date(post.created_at).toLocaleDateString()}</span>
                <span>👁️ {post.views}</span>
                <span>❤️ {post.favorites_count}</span>
              </div>
              <p className="post-excerpt">{post.excerpt}</p>
              <Link to={`/post/${post.id}`} className="read-more">Читать далее →</Link>
            </div>
          </div>
        ))}
      </div>

      <div className="pagination">
        <button onClick={handlePrev} disabled={!prevPageUrl} className="page-btn">
          ← Назад
        </button>
        <button onClick={handleNext} disabled={!nextPageUrl} className="page-btn">
          Вперёд →
        </button>
      </div>
    </div>
  );
}