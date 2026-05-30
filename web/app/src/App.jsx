import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import Login from './pages/Login.jsx'
import Callback from './pages/Callback.jsx'
import HomePage from './pages/HomePage.jsx';
import Chatbot from './pages/Chatbot.jsx';
import Profile from './pages/Profile.jsx'
import AACTTPlan from './pages/Plan.jsx';
import Frailty from './pages/Frailty.jsx';
import Assessment from './pages/Asessment.jsx';
import Leaderboard from './pages/Leaderboard.jsx';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/callback" element={<Callback />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/chatbot" element={<Chatbot />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/plan" element={<AACTTPlan />} />
        <Route path="/frailty" element={<Frailty />} />
        <Route path="/assessment" element={<Assessment />} />
        <Route path="/leaderboard" element={<Leaderboard />} />

        <Route path="*" element={<Navigate to="/login" replace />} /> 
      </Routes>
    </BrowserRouter>
  );
}

export default App;
