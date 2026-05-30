import { useState, useEffect } from "react";
import '@material/web/icon/icon.js';

function ShowScore() {
  const [score, setScore] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const getProfile = async () => {
      try {
        const response = await fetch('https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/profile', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + sessionStorage.getItem("id_token"),
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        setScore(result.profile.activity_score);

      } catch (e) {
        console.error(e.message);
      }

      setLoading(false);
    }

    getProfile();
  }, []);

  if (loading) {
    return (
      <div className="center-txt">
        <md-circular-progress indeterminate></md-circular-progress>
        Loading...
      </div>
    )
  }

  return (
    <div className="content">
      <div className="plan-header">
        <h3>Your activity score:</h3>
        <div className="plan-header">
          <h2>{score}</h2>
          <md-icon>trophy</md-icon>
        </div>
      </div>
    </div>
  )
}

function Score() {
  return <ShowScore />
}

export default Score;