import React, { useState, useEffect } from 'react';
import { Route, Routes, useNavigate, useLocation, Navigate } from 'react-router-dom';
import './App.css';
import logo from './assets/logo.svg';
import avatar from './assets/avatar.svg';

// Import des composants
import Button from './components/Button';
import Card from './components/Card';
import Input from './components/Input';
import Loader from './components/Loader';
import Navbar from './components/Navbar/Navbar';
import Sidebar from './components/Sidebar/Sidebar';
import SearchBar from './components/SearchBar/SearchBar';
import PrivateRoute from './components/PrivateRoute';
import NotificationContainer from './components/Notification/NotificationContainer';

// Import du contexte
import { useAppContext } from './context/AppContext';
import { useAuth } from './context/AuthContext';
import { NotificationProvider, useNotification } from './context/NotificationContext';

// Import des pages
import HomePage from './pages/HomePage';
import DocumentsPage from './pages/DocumentsPage';
import DocumentEditorPage from './pages/DocumentEditorPage';
import TemplatesPage from './pages/TemplatesPage';
import CategoriesPage from './pages/CategoriesPage';
import UsersPage from './pages/UsersPage';
import ContactsPage from './pages/ContactsPage';
import SharePage from './pages/SharePage';
import StatsPage from './pages/StatsPage';
import TrashPage from './pages/TrashPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import VynalGPTPage from './pages/VynalGPTPage';
import SettingsPage from './pages/SettingsPage';

const MainApp = () => {
  const { 
    activeSection, 
    setActiveSection, 
    isLoading,
    documents,
    activities,
    darkMode,
    toggleDarkMode,
    sidebarVisible
  } = useAppContext();
  
  const { user, logout } = useAuth();
  const { 
    notifications, 
    unreadCount, 
    success, 
    error, 
    warning, 
    info, 
    clearAllNotifications,
    removeNotification,
    markAsRead
  } = useNotification();
  
  const [searchQuery, setSearchQuery] = useState('');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  
  const navigate = useNavigate();
  const location = useLocation();
  
  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success':
        return 'bx-check-circle';
      case 'error':
        return 'bx-x-circle';
      case 'warning':
        return 'bx-error';
      case 'info':
        return 'bx-info-circle';
      default:
        return 'bx-bell';
    }
  };
  
  // Synchroniser la section active avec le chemin de l'URL
  useEffect(() => {
    const path = location.pathname.substring(1) || 'dashboard';
    if (path !== activeSection) {
      setActiveSection(path);
    }
  }, [location, activeSection, setActiveSection]);
  
  // Gestionnaires d'événements explicites
  const handleSectionClick = (section) => {
    setActiveSection(section);
    if (section === 'dashboard') {
      clearAllNotifications();
    }
    navigate(`/${section === 'dashboard' ? '' : section}`);
  };
  
  const handleBellClick = () => {
    setShowNotifications(!showNotifications);
  };
  
  const handleSettingsClick = () => {
    console.log('Settings clicked');
    navigate('/settings');
  };
  
  const handleDarkModeClick = () => {
    toggleDarkMode();
  };
  
  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
  };
  
  const handleUserMenuClick = () => {
    setShowUserMenu(!showUserMenu);
  };
  
  const handleProfileClick = () => {
    alert('Profil utilisateur');
    setShowUserMenu(false);
  };
  
  const handleSettingsMenuClick = () => {
    navigate('/settings');
    setShowUserMenu(false);
  };
  
  const handleLogoutClick = () => {
    logout();
    navigate('/login');
    setShowUserMenu(false);
  };
  
  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      alert(`Recherche de: ${searchQuery}`);
      // Implémenter la recherche
    }
  };
  
  return (
    <div className={`app ${darkMode ? 'dark-mode' : ''}`}>
      <Navbar 
        onDarkModeToggle={toggleDarkMode} 
        darkMode={darkMode} 
        user={user}
      >
        <div className="logo" onClick={() => handleSectionClick('dashboard')}>
          <img src={logo} alt="Vynal Docs" className="logo-image" />
          <h1 className="logo-text">Vynal Docs</h1>
        </div>
        <SearchBar placeholder="Rechercher..." />
        <div className="navbar-actions">
          <Button variant="transparent" onClick={handleDarkModeClick} className="dark-mode-toggle">
            <i className={`bx ${darkMode ? 'bx-sun' : 'bx-moon'}`}></i>
          </Button>
          <Button variant="transparent" onClick={handleSettingsClick}>
            <i className='bx bx-cog'></i>
          </Button>
          <div className="notification-wrapper">
            <Button variant="transparent" onClick={handleBellClick}>
              <i className='bx bx-bell'></i>
              {unreadCount > 0 && (
                <span className="notification-badge">{unreadCount}</span>
              )}
            </Button>
            {showNotifications && (
              <div className="notification-dropdown">
                <div className="notification-header">
                  <h3>Notifications</h3>
                  {notifications.length > 0 && (
                    <button onClick={clearAllNotifications} className="clear-all">
                      Tout effacer
                    </button>
                  )}
                </div>
                <div className="notification-list">
                  {notifications.length === 0 ? (
                    <div className="no-notifications">
                      Aucune notification
                    </div>
                  ) : (
                    notifications.map(notification => (
                      <div 
                        key={notification.id} 
                        className={`notification-item ${notification.read ? 'read' : 'unread'}`}
                        onClick={() => markAsRead(notification.id)}
                      >
                        <div className="notification-icon">
                          <i className={`bx ${getNotificationIcon(notification.type)}`}></i>
                        </div>
                        <div className="notification-content">
                          <div className="notification-title">{notification.title}</div>
                          <div className="notification-message">{notification.message}</div>
                        </div>
                        <button 
                          className="notification-close"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeNotification(notification.id);
                          }}
                        >
                          <i className="bx bx-x"></i>
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
          <div className="user-profile" onClick={handleUserMenuClick}>
            <img src={user?.avatar || avatar} alt="User Avatar" className="user-avatar" />
            <span className="user-name">{user?.name || 'Utilisateur'}</span>
            {showUserMenu && (
              <div className="user-dropdown">
                <div className="user-dropdown-header">
                  <img src={user?.avatar || avatar} alt="User Avatar" className="user-dropdown-avatar" />
                  <div className="user-dropdown-info">
                    <div className="user-dropdown-name">{user?.name || 'Utilisateur'}</div>
                    <div className="user-dropdown-email">{user?.email || 'email@example.com'}</div>
                  </div>
                </div>
                <div className="user-dropdown-divider"></div>
                <div className="user-dropdown-item" onClick={handleProfileClick}>
                  <i className="bx bx-user"></i> Profil
                </div>
                <div className="user-dropdown-item" onClick={handleSettingsMenuClick}>
                  <i className="bx bx-cog"></i> Paramètres
                </div>
                <div className="user-dropdown-divider"></div>
                <div className="user-dropdown-item" onClick={handleLogoutClick}>
                  <i className="bx bx-log-out"></i> Déconnexion
                </div>
              </div>
            )}
          </div>
        </div>
      </Navbar>
      
      <div className={`main-content ${!sidebarVisible ? 'sidebar-hidden' : ''}`}>
        <Sidebar onSectionClick={handleSectionClick} activeSection={activeSection} />
        
        <div className="content-area">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/documents/edit/:documentId" element={<DocumentEditorPage />} />
            <Route path="/documents/new" element={<DocumentEditorPage />} />
            <Route path="/templates" element={<TemplatesPage />} />
            <Route path="/categories" element={<CategoriesPage />} />
            <Route path="/users" element={<UsersPage />} />
            <Route path="/contacts" element={<ContactsPage />} />
            <Route path="/share" element={<SharePage />} />
            <Route path="/stats" element={<StatsPage />} />
            <Route path="/trash" element={<TrashPage />} />
            <Route path="/vynalgpt" element={<VynalGPTPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
      </div>
    </div>
  );
};

const App = () => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <Loader text="Chargement..." />
      </div>
    );
  }
  
  return (
    <NotificationProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        <Route path="/*" element={
          isAuthenticated ? <MainApp /> : <Navigate to="/login" />
        } />
      </Routes>
    </NotificationProvider>
  );
};

export default App;
