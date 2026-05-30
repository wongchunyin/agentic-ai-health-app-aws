import { useState, useEffect } from "react";
import { useNavigate } from 'react-router-dom';
import '@material/web/button/filled-button.js';
import '@material/web/radio/radio.js';
import '@material/web/checkbox/checkbox.js';
import '@material/web/progress/circular-progress.js';

function AssessmentForm() {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  const params = new URLSearchParams(location.search);
  const assessment_type = params.get('assessment_type');

  useEffect(() => {
    const getQuestions = async () => {
      try {
        const response = await fetch(`https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/assessments/questions/${assessment_type}`, {
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
        setQuestions(result);

      } catch (e) {
        console.error(e.message);
      }
    }

    const getAnswers = async () => {
      const params = new URLSearchParams(location.search);
      const assessment_id = params.get('assessment_id');
      if (assessment_id) {
        try {
          const response = await fetch(`https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/assessments/${assessment_id}`, {
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
          setAnswers(result.assessment_data);

        } catch (e) {
          console.error(e.message);
        }
      }
      setLoading(false);
    }

    getQuestions();
    getAnswers();
  }, []);

  const handleChange = (key, value, multiple = false) => {
    setAnswers((prev) => {
      if (multiple) {
        const current = prev[key] || [];
        return {
          ...prev,
          [key]: current.includes(value)
            ? current.filter((v) => v !== value)
            : [...current, value],
        };
      }
      return { ...prev, [key]: value };
    });
  };

  if (loading) {
    return (
      <div className="center-txt">
        <md-circular-progress indeterminate></md-circular-progress>
        Loading...
      </div>
    )
  }

  const handleSave = () => {
    setSaving(true);
    const data = {
      assessment_type: assessment_type,
      assessment_data: answers
    };
    if (assessment_type === "FRAIL" && !data.assessment_data.illnesses) {
      data.assessment_data.illnesses = [];
    }

    const saveAssessment = async () => {
      const params = new URLSearchParams(location.search);
      const assessment_id = params.get('assessment_id');
      if (assessment_id) {
        try {
          const response = await fetch(`https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/assessments/${assessment_id}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer ' + sessionStorage.getItem("id_token"),
            },
            body: JSON.stringify(data),
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          navigate('/frailty');

        } catch (e) {
          console.error(e.message);
        }
      } else {
        try {
          const response = await fetch('https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/assessments', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer ' + sessionStorage.getItem("id_token"),
            },
            body: JSON.stringify(data),
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          navigate('/frailty');

        } catch (e) {
          console.error(e.message);
        }
      }
      setSaving(false);
    }

    saveAssessment();
  };

  return (
    <div className="content">
      {assessment_type === "FRAIL" ? <h2>FRAIL scale questionnaire</h2> : <h2>Rockwood-Mitnitski frailty index</h2>}
      {Object.entries(questions).map(([key, item]) => (
        <div key={item.question} className="label">
          <p>{item.question}</p>
          {key === "illnesses" ? (
            item.options.map((opt) => (
              <div key={opt.value} className="label">
                <md-checkbox
                  value={opt.value}
                  checked={(answers[key] || []).includes(opt.value)}
                  onChange={() => handleChange(key, opt.value, true)}
                />
                <label>{opt.label}</label>
              </div>
            ))
          ) : (
            item.options.map((opt) => (
              <div key={opt.value} className="label">
                <md-radio
                  name={key}
                  value={opt.value}
                  checked={answers[key] === opt.value}
                  onChange={() => handleChange(key, opt.value)}
                />
                <label>{opt.label}</label>
              </div>
            ))
          )}
        </div>
      ))}
      <div>
        {!saving ? (
          <md-filled-button className="btn-right" onClick={handleSave}>Save</md-filled-button>
        ) : (
          <div className="btn-right">
            <md-circular-progress indeterminate></md-circular-progress>
            Saving...
          </div>
        )}
      </div>
    </div>
  );
}

export default AssessmentForm;