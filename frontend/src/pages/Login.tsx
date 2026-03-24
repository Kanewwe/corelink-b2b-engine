import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { fetchWithAuth } from '../services/api';

const Login: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ email: '', password: '', username: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleToggle = () => setIsLogin(!isLogin);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const body = isLogin 
        ? { email: formData.email, password: formData.password }
        : { email: formData.email, password: formData.password, username: formData.username };

      const response = await fetchWithAuth(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body) // Using normal JSON post per typical refactor, ensure backend accepts if it used Form data before
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || 'Login failed');
      }

      login(data.user, data.access_token);
      navigate('/lead-engine');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-bg-dark text-text-main">
      <div className="w-full max-w-md p-8 glass-panel animate-in zoom-in-95 duration-300">
        <div className="flex justify-center mb-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent shadow-[0_0_15px_rgba(79,142,247,0.4)]"></div>
            <h1 className="text-2xl font-bold bg-gradient-to-br from-primary to-accent bg-clip-text text-transparent">Linkora</h1>
          </div>
        </div>
        <h2 className="text-xl text-center font-semibold mb-6">
          {isLogin ? 'Sign In to Proceed' : 'Create an Account'}
        </h2>
        {error && <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-3 rounded-lg text-sm mb-4">{error}</div>}
        
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {!isLogin && (
            <div>
              <label className="block text-sm text-text-muted mb-1">Username</label>
              <input 
                type="text" 
                required 
                className="w-full p-2.5 bg-black/25 border border-glass-border rounded-lg focus:outline-none focus:border-primary transition-all"
                value={formData.username}
                onChange={e => setFormData({...formData, username: e.target.value})}
              />
            </div>
          )}
          <div>
            <label className="block text-sm text-text-muted mb-1">Email</label>
            <input 
              type="email" 
              required 
              className="w-full p-2.5 bg-black/25 border border-glass-border rounded-lg focus:outline-none focus:border-primary transition-all"
              value={formData.email}
              onChange={e => setFormData({...formData, email: e.target.value})}
            />
          </div>
          <div>
            <label className="block text-sm text-text-muted mb-1">Password</label>
            <input 
              type="password" 
              required 
              className="w-full p-2.5 bg-black/25 border border-glass-border rounded-lg focus:outline-none focus:border-primary transition-all"
              value={formData.password}
              onChange={e => setFormData({...formData, password: e.target.value})}
            />
          </div>
          <button type="submit" disabled={loading} className="btn-primary mt-2 flex justify-center items-center py-2.5">
            {loading ? <span className="animate-spin text-xl">↻</span> : (isLogin ? 'Sign In' : 'Sign Up')}
          </button>
        </form>
        
        <p className="text-center text-sm text-text-muted mt-6">
          {isLogin ? "Don't have an account? " : "Already have an account? "}
          <button type="button" onClick={handleToggle} className="text-primary hover:underline font-medium">
            {isLogin ? 'Register Here' : 'Log In'}
          </button>
        </p>
      </div>
    </div>
  );
};

export default Login;
