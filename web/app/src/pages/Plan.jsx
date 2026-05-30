import { useState, useEffect } from "react";
import { useNavigate } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import Header from '../components/Header.jsx';
import '@material/web/button/filled-button.js';
import '@material/web/button/outlined-button.js';
import '@material/web/button/text-button.js';
import '@material/web/textfield/outlined-text-field.js';
import '@material/web/select/outlined-select.js';
import '@material/web/select/select-option.js';
import '@material/web/dialog/dialog.js';
import '@material/web/progress/circular-progress.js';

function PlanForm() {
  const id = uuidv4();
  const [plan, setPlan] = useState({
    action: {
      name: '',
      description: '',
    },
    actor: 'user',
    context: {
      location: '',
      condition: '',
    },
    target: '',
    time: {
      frequency: {
        value: '',
        unit: '',
      },
      duration: {
        value: '',
        unit: '',
      }
    },
    plan_id: id,
    plan_type: "manually_created"
  });
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState(plan);
  const [showWarning, setShowWarning] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  const params = new URLSearchParams(location.search);
  const plan_id = params.get('plan_id');

  useEffect(() => {
    const getPlan = async () => {
      try {
        const response = await fetch(`https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/plans/${plan_id}`, {
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

        setPlan(result.plan);
        setFormData(result.plan);

      } catch (e) {
        console.error(e.message);
      }
      setLoading(false);
    }

    if (plan_id) {
      getPlan();
    } else {
      setLoading(false);
    };
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    const keys = name.split('.');
    setFormData((prevData) => {
      let newData = { ...prevData };
      let currentData = newData;
      for (let i = 0; i < keys.length - 1; i++) {
        currentData[keys[i]] = { ...currentData[keys[i]] };
        currentData = currentData[keys[i]];
      }
      currentData[keys[keys.length - 1]] = value;
      return newData;
    });
  };

  if (loading) {
    return (
      <div className="center-txt">
        <md-circular-progress indeterminate></md-circular-progress>
        Loading...
      </div>
    )
  };

  const handleSubmit = () => {
    setSaving(true);
    
    const savePlan = async () => {
      if (plan_id) {
        try {
          const response = await fetch(`https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/plans/${plan_id}`, {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer ' + sessionStorage.getItem("id_token"),
            },
            body: JSON.stringify(formData),
          });

          if (!response.ok) {
            const error = await response.json();
            if (error.reason) {
              setErrorMessage(error.reason);
            } else {
              setErrorMessage(error.error);
            }
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          navigate('/home');

        } catch (e) {
          const error = await response.json();
          setErrorMessage(error.error);
          setShowWarning(true);
        }
      } else {
        const data = {
          plan_data: formData
        }
        try {
          const response = await fetch(`https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/plans`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer ' + sessionStorage.getItem("id_token"),
            },
            body: JSON.stringify(data),
          });

          if (!response.ok) {
            const error = await response.json();
            if (error.reason) {
              setErrorMessage(error.reason);
            } else {
              setErrorMessage(error.error);
            }
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          navigate('/home');

        } catch (e) {
          console.error(e.message);
          setShowWarning(true);
        }
      }

      setSaving(false);
    };

    savePlan();
  };

  return (
    <div>
      <md-dialog open={showWarning}>
        <div slot="headline">Error</div>
        <div slot="content">
          <p>{errorMessage}</p>
        </div>
        <div slot="actions">
          <md-text-button onClick={() => setShowWarning(false)}>Close</md-text-button>
        </div>
      </md-dialog>

      <div className="content">
        <h2>Action</h2>
        <md-outlined-text-field
          label="Name"
          name="action.name"
          value={formData.action.name}
          onChange={handleChange}
        // required
        />
        <md-outlined-text-field
          label="Description"
          name="action.description"
          value={formData.action.description}
          onChange={handleChange}
        // required
        />
        <h2>Context</h2>
        <md-outlined-text-field
          label="Location"
          name="context.location"
          value={formData.context.location}
          onChange={handleChange}
        // required
        />
        <md-outlined-text-field
          label="Condition"
          name="context.condition"
          value={formData.context.condition}
          onChange={handleChange}
        // required
        />
        <h2>Target</h2>
        <md-outlined-text-field
          label="Target"
          name="target"
          value={formData.target}
          onChange={handleChange}
        // required
        />
        <h2>Time</h2>
        <p>Frequency</p>
        <div className="flex-row">
          <md-outlined-text-field
            label="Value"
            name="time.frequency.value"
            value={formData.time.frequency.value}
            onChange={handleChange}
          // required
          />
          <md-outlined-select label="Unit" name="time.frequency.unit" value={formData.time.frequency.unit} onChange={handleChange}>
            <md-select-option value="per day">per day</md-select-option>
            <md-select-option value="per week">per week</md-select-option>
          </md-outlined-select>
        </div>
        <p>Duration</p>
        <div className="flex-row">
          <md-outlined-text-field
            label="Value"
            name="time.duration.value"
            value={formData.time.duration.value}
            onChange={handleChange}
          // required
          />
          <md-outlined-select label="Unit" name="time.duration.unit" value={formData.time.duration.unit} onChange={handleChange}>
            <md-select-option value="minutes">minutes</md-select-option>
            <md-select-option value="hours">hours</md-select-option>
          </md-outlined-select>
        </div>
        <div>
          {!saving ? (
            <md-filled-button className='btn-right' onClick={() => handleSubmit()}>Save plan</md-filled-button>
          ) : (
            <div className='btn-right'>
              <md-circular-progress indeterminate></md-circular-progress>
              Saving...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PlanPrompt() {
  const [type, setType] = useState({
    action_type: 'physical'
  });
  const [manual, setManual] = useState(false);
  const [generating, setGenerating] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { value } = e.target;
    setType({ ...type, action_type: value });
  };

  const handleSubmit = () => {
    setGenerating(true);

    const generatePlan = async () => {
      try {
        const response = await fetch(`https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/aactt/generate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + sessionStorage.getItem("id_token"),
          },
          body: JSON.stringify(type),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        const data = {
          plan_data: result
        }

        try {
          const response = await fetch(`https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/plans`, {
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

          navigate('/home');

        } catch (e) {
          console.error(e.message);
        }

      } catch (e) {
        console.error(e.message);
      }

      setGenerating(false);
    };

    generatePlan();
  }

  const handleEdit = () => {
    setManual(true);
  };

  if (manual) {
    return <PlanForm />;
  };

  return (
    <div className="prompt">
      <p>Select a plan action type:</p>
      <md-outlined-select label="Type" value={type.action_type} onChange={handleChange}>
        <md-select-option value="physical">Physical</md-select-option>
        <md-select-option value="mental">Mental</md-select-option>
        <md-select-option value="diet">Diet</md-select-option>
      </md-outlined-select>
      {!generating ? (
        <md-filled-button className="btn-center" onClick={() => handleSubmit()}>Generate plan</md-filled-button>
      ) : (
        <div>
          <md-circular-progress indeterminate></md-circular-progress>
          Generating...
        </div>
      )}
      <md-outlined-button className="btn-center" onClick={() => handleEdit()} disabled={generating}>I'd like to create my own plan</md-outlined-button>
    </div>
  )
}

function AACTTPlan() {
  const params = new URLSearchParams(location.search);
  const plan_id = params.get('plan_id');

  return (
    <div>
      <Header />
      <main>
        {plan_id ? (
          <div>
            <h2>Edit plan</h2>
            <PlanForm />
          </div>
        ) : (
          <div>
            <h2>Create plan</h2>
            <PlanPrompt />
          </div>
        )}
      </main>
    </div>
  );
}

export default AACTTPlan;
