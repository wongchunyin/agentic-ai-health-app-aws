import { useState, useEffect } from "react";
import { Link, useNavigate } from 'react-router-dom';
import '@material/web/button/filled-button.js';
import '@material/web/button/outlined-button.js';
import '@material/web/progress/linear-progress.js';
import '@material/web/progress/circular-progress.js';
import '@material/web/icon/icon.js';

function ListPlans({ items }) {
  const [activeIndex, setActiveIndex] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  const handleToggle = (index) => {
    setActiveIndex(index === activeIndex ? null : index);
  };

  const handleEdit = (e, index) => {
    e.stopPropagation();
    const planId = JSON.parse(sessionStorage.getItem("plans"))[index].plan_id;

    navigate(`/plan?plan_id=${planId}`);
  };

  const handleDelete = (e, index) => {
    e.stopPropagation();
    setDeleting(true);
    const planId = JSON.parse(sessionStorage.getItem("plans"))[index].plan_id;

    const deletePlan = async (planId) => {
      try {
        const response = await fetch(`https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/plans/${planId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + sessionStorage.getItem("id_token"),
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        window.location.reload();

      } catch (e) {
        console.error(e.message);
      }

      setDeleting(false);
    }

    deletePlan(planId);
  };

  const handleComplete = (e, index) => {
    e.stopPropagation();
    setSaving(true);
    const planId = JSON.parse(sessionStorage.getItem("plans"))[index].plan_id;

    const planComplete = async () => {
      try {
        const response = await fetch(`https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/increment-activity?plan_id=${planId}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + sessionStorage.getItem("id_token"),
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        window.location.reload();

      } catch (e) {
        console.error(e.message);
      }

      setSaving(false);
    }

    planComplete();
  };

  const tasks = JSON.parse(sessionStorage.getItem("tasks"));

  return (
    <div>
      {items.map((item, index) => {
        const isActive = activeIndex === index;
        const task = tasks.find(t => t.plan_id === item.plan_id);
        const progress = task.cnt_activity_done / task.target;
        return (
          <div key={index}>
            <div className="plan" onClick={() => handleToggle(index)}>
              <div className="plan-header">
                <h3>{item.action.name}</h3>
                <div className="plan-header">
                  <md-linear-progress value={progress}></md-linear-progress>
                  <span>{isActive ? "🞁" : "🞃"}</span>
                </div>
              </div>

              {activeIndex === index && (
                <div className="plan-content">
                  <p><b>
                    {item.time.duration ? <span>{item.time.duration.value} </span> : null}
                    {item.time.duration ? <span>{item.time.duration.unit}, </span> : null}
                    <span>{item.time.frequency.value} </span>
                    <span>{item.time.frequency.unit}, </span>
                    {item.context.location}
                  </b></p>
                  <p>{item.action.description}</p>
                  <p>{item.context.condition}</p>
                  <div>
                    <md-filled-button className="btn-left" onClick={(e) => handleEdit(e, index)} disabled={deleting}>
                      Edit
                      <md-icon slot="icon">edit</md-icon>
                    </md-filled-button>
                    {!deleting ? (
                      <md-outlined-button className="btn-left" onClick={(e) => handleDelete(e, index)}>
                        Delete
                        <md-icon slot="icon">delete</md-icon>
                      </md-outlined-button>
                    ) : (
                      <>
                        <md-circular-progress indeterminate></md-circular-progress>
                        Deleting...
                      </>
                    )}
                    {!saving ? (
                      <md-filled-button className="btn-right" onClick={(e) => handleComplete(e, index)} disabled={deleting}>
                        Mark complete
                        <md-icon slot="icon">check_circle</md-icon>
                      </md-filled-button>
                    ) : (
                      <div className="btn-right">
                        <md-circular-progress indeterminate></md-circular-progress>
                        Saving...
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function Plans() {
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [loadingTasks, setLoadingTasks] = useState(true);

  useEffect(() => {
    const getPlans = async () => {
      try {
        const response = await fetch('https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/plans?all=true', {
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
        sessionStorage.setItem("plans", JSON.stringify(result.plans));

      } catch (e) {
        console.error(e.message);
      }

      setLoadingPlans(false);
    }

    const getTasks = async () => {
      try {
        const response = await fetch('https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/schedule-tasks', {
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
        sessionStorage.setItem("tasks", JSON.stringify(result.tasks));

      } catch (e) {
        console.error(e.message);
      }

      setLoadingTasks(false);
    }

    getPlans();
    getTasks();
  }, []);

  if (loadingPlans || loadingTasks) {
    return (
      <div className="center-txt">
        <md-circular-progress indeterminate></md-circular-progress>
        Loading...
      </div>
    )
  }

  const items = JSON.parse(sessionStorage.getItem("plans"));

  if (items && items.length > 0) {
    return (
      <div className="plan-list">
        <ListPlans items={items} />
        <Link to="/plan">
          <md-filled-button className='btn-right'>
            New plan
            <md-icon slot="icon">add</md-icon>
          </md-filled-button>
        </Link>
      </div>
    );
  } else {
    return (
      <div className="prompt">
        <p>Looks like you have no plans. Create one now!</p>
        <Link to="/plan">
          <md-filled-button>Create plan</md-filled-button>
        </Link>
      </div>
    );
  }
}

export default Plans;