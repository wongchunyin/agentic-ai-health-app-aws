import { useState, useEffect } from "react";
import { Link, useNavigate } from 'react-router-dom';
import Header from '../components/Header.jsx';
import '@material/web/button/filled-button.js';

function ShowAssessments() {
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const getAssessments = async () => {
      try {
        const response = await fetch('https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/assessments/all', {
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
        result.sort((a, b) => new Date(b.metadata.updated_at) - new Date(a.metadata.updated_at));
        sessionStorage.setItem("assessments", JSON.stringify(result));

      } catch (e) {
        console.error(e.message);
      }

      setLoading(false);
    }

    getAssessments();
  }, []);

  const handleUpdate = (e, index) => {
    const assessmentId = JSON.parse(sessionStorage.getItem("assessments"))[index].assessment_id;
    const assessmentType = JSON.parse(sessionStorage.getItem("assessments"))[index].assessment_type;
    
    navigate(`/assessment?assessment_id=${assessmentId}&assessment_type=${assessmentType}`);
  }

  if (loading) {
    return (
      <div className="center-txt">
        <md-circular-progress indeterminate></md-circular-progress>
        Loading...
      </div>
    )
  }

  const items = JSON.parse(sessionStorage.getItem("assessments"));

  if (items && items.length > 0) {
    return (
      <div>
        <div className="content">
          {items[0].status === "completed" ? (
            <div>
              <h2>Assessment:</h2>
              <h1>{items[0].assessment_result.level}</h1>
              <p><b>Assessment type: </b>{items[0].assessment_type}</p>
              <p><b>Date: </b>{items[0].metadata.updated_at.split('T')[0]}</p>
              <Link to="/assessment" className="btn-left">
                <md-filled-button>Take another assessment</md-filled-button>
              </Link>
            </div>
          ) : (
            <div>
              <h2>Status:</h2>
              <h1>Incomplete</h1>
              <p><b>Assessment type: </b>{items[0].assessment_type}</p>
              <p><b>Date: </b>{items[0].metadata.updated_at.split('T')[0]}</p>
              <md-filled-button className="btn-left" onClick={(e) => handleUpdate(e, 0)}>Update</md-filled-button>
            </div>
          )}
        </div>

        <h2>Recent assessments</h2>
        <div className="plan-list">
          {items.slice(1, 6).map((item, index) => {
            const date = item.metadata.updated_at.split('T')[0];
            return (
              <div key={index}>
                <div className="plan">
                  <div className="plan-header">
                    <div>
                      <h3>{date}</h3>
                      <p><b>Assessment type: </b>{item.assessment_type}</p>
                    </div>
                    {item.status === "completed" ? <h3>{item.assessment_result.level}</h3> : <md-filled-button onClick={(e) => handleUpdate(e, index + 1)}>Continue</md-filled-button>}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  } else {
    return (
      <div className="prompt">
        <p>Looks like you have no assessments. Take one now!</p>
        <Link to="/assessment">
          <md-filled-button>Take assessment</md-filled-button>
        </Link>
      </div>
    );
  }
}

function Frailty() {
  return (
    <div>
      <Header />
      <main>
        <h2>Frailty Assessments</h2>
        <ShowAssessments />
      </main>
    </div>
  );
}

export default Frailty;