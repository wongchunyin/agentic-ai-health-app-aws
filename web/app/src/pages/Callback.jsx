import { useEffect, useRef } from 'react';
import { useLocation, useNavigate, Navigate } from 'react-router-dom';

function Callback() {
  const location = useLocation();
  const navigate = useNavigate();
  const effect = useRef(false);

  useEffect(() => {
    if (!effect.current) {
      effect.current = true;
      const params = new URLSearchParams(location.search);
      const code = params.get('code');
      if (code) {
        getTokens(code);
      } else {
        console.log('No authorization code found in URL.');
      }
    }
  }, [location, navigate]);

  const getTokens = async (code) => {
    try {
      const response = await fetch('https://livewell.auth.us-east-1.amazoncognito.com/oauth2/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          grant_type: 'authorization_code',
          client_id: '2n6ggumluvpk831jkl2a119rl1',
          code: code,
          // redirect_uri: 'https://d3jkj7lzcnesij.cloudfront.net/callback',
          redirect_uri: 'http://localhost:5173/callback',
        }).toString()
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      sessionStorage.setItem('id_token', result.id_token);
      sessionStorage.setItem('access_token', result.access_token);
      sessionStorage.setItem('refresh_token', result.refresh_token);

      navigate('/home', { replace: true });

    } catch (error) {
      console.error('Error exchanging code for tokens:', error);
    }
  }
}

export default Callback;