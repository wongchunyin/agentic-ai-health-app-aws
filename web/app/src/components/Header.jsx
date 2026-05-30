import { Link } from 'react-router-dom';
import React, { useState } from 'react';

function Settings() {
  const [theme, setTheme] = useState('light');
  const [textSize, setTextSize] = useState('small');

  const changeTheme = () => {
    if (theme === 'light') {
      setTheme('dark');
    } else {
      setTheme('light');
    }
    document.documentElement.style.setProperty('--background-color', theme === 'light' ? '#333' : '#fff');
    document.documentElement.style.setProperty('--text-color', theme === 'light' ? '#fff' : '#333');
    console.log("Theme changed.")
  };

  const changeTextSize = () => {
    if (textSize === 'small') {
      setTextSize('medium');
      document.documentElement.style.setProperty('--font-size-base', '20px');
    } else if (textSize === 'medium') {
      setTextSize('large');
      document.documentElement.style.setProperty('--font-size-base', '22px');
    } else {
      setTextSize('small');
      document.documentElement.style.setProperty('--font-size-base', '18px');
    }
    console.log("Text size changed.")
  };

  return (
    <div className="dropdown">
      <button className="dropbtn">
        <img src="/icons/settings_icon.png" width="50" height="50" />
      </button>
      <div className="dropdown-content">
        <a onClick={changeTheme}>Change theme</a> 
        <a onClick={changeTextSize}>Change text size</a>
      </div>
    </div>
  );
}

function Profile() {
  const handleLogout = () => {
      sessionStorage.clear()
      console.log("Session storage cleared.")

      // const cognitoLogoutUrl = "https://livewell.auth.us-east-1.amazoncognito.com/logout?client_id=2n6ggumluvpk831jkl2a119rl1&response_type=code&scope=email+openid+phone&logout_uri=https%3A%2F%2Fd3jkj7lzcnesij.cloudfront.net%2Flogin"
      const cognitoLogoutUrl = "https://livewell.auth.us-east-1.amazoncognito.com/logout?client_id=2n6ggumluvpk831jkl2a119rl1&logout_uri=http%3A%2F%2Flocalhost%3A5173%2Flogin&response_type=code&scope=email+openid+phone";
      window.location.href = cognitoLogoutUrl;
    };
  
  return (
    <div className="dropdown">
      <button className="dropbtn">
        <img src="/icons/profile_icon.png" width="40" height="40" />
      </button>
      <div className="dropdown-content">
        <Link to="/profile">Profile</Link>
        <a onClick={handleLogout}>Logout</a>
      </div>
    </div>
  );
}

function Header() {
  return (
    <header>
      <div className="left-header-content">
        <div className="logo-white">
          <Link to="/home">
            <img src="/logo/logo.png" width="120" height="60" />
          </Link>
        </div>
        <nav>
          <Link to="/home">
            <img src="/icons/home_icon.png" width="30" height="30" />
            <p>Home</p>
          </Link>
          <Link to="/chatbot">
            <img src="/icons/chatbot_icon.png" width="30" height="30" />
            <p>AI Agent</p>
          </Link>
          <Link to="/frailty">
            <img src="/icons/frailty_icon.png" width="30" height="30" />
            <p>Frailty</p>
          </Link>
          <Link to="/leaderboard">
            <img src="/icons/leaderboard_icon.png" width="30" height="30" />
            <p>Leaderboard</p>
          </Link>
        </nav>
      </div>
      <div className="right-header-content">
        <nav>
          <Settings />
          <Profile />
        </nav>
      </div>
    </header>
  );
}

export default Header;
