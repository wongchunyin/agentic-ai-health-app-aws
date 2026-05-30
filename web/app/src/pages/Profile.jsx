import { useState, useEffect } from "react";
import Header from '../components/Header.jsx';
import '@material/web/button/filled-button.js';
import '@material/web/button/outlined-button.js';
import '@material/web/textfield/outlined-text-field.js';
import '@material/web/checkbox/checkbox.js';
import '@material/web/icon/icon.js';
import '@material/web/progress/circular-progress.js';

function PersonalInfo() {
  const [loading, setLoading] = useState(true);
  const [showWarning, setShowWarning] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [saving, setSaving] = useState(false);

  let userEmail = "";
  const token = sessionStorage.getItem("id_token");
  if (token) {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const decodedPayload = JSON.parse(window.atob(base64));
      userEmail = decodedPayload.email;
    } catch (error) {
      console.error("Error decoding token:", error);
    }
  } else {
    console.log("No token found.");
  }

  const [profile, setProfile] = useState({
    email: userEmail,
    first_name: "",
    family_name: "",
    email_permission: false,
    allowShareName: false,
    address: {
      city: "",
      country: "",
    }
  });

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

        if (result.profile.address === null) {
          result.profile.address = {
            city: "",
            country: "",
          };
        }

        setProfile(prev => ({
          ...prev,
          ...result.profile,
        }));

      } catch (e) {
        console.error(e.message);
      }

      setLoading(false);
    }

    getProfile();
  }, []);

  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState(profile);

  const handleChange = (e) => {
    const { name, value } = e.target;
    const nameParts = name.split('.');
    if (nameParts.length === 1) {
      setFormData((prevData) => ({
        ...prevData,
        [name]: value.trim()
      }));
    } else {
      const topLevelKey = nameParts[0];
      const nestedKey = nameParts[1];
      setFormData(prevData => ({
        ...prevData,
        [topLevelKey]: {
          ...prevData[topLevelKey],
          [nestedKey]: value.trim()
        }
      }));
    }
  };

  const handleCheck = (e) => {
    const { name, checked } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: checked
    }));
  }

  const handleSave = () => {
    setSaving(true);
    const data = formData;
    data.full_name = `${data.first_name} ${data.family_name}`;

    const saveProfile = async () => {
      try {
        const response = await fetch('https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/profile', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + sessionStorage.getItem("id_token"),
          },
          body: JSON.stringify(data),
        });

        if (!response.ok) {
          const error = await response.json();
          setErrorMessage(await error.error);
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        window.location.reload();

      } catch (e) {
        console.error(e.message);
        setShowWarning(true);
      }

      setSaving(false);
    }

    saveProfile();
  };

  const handleCancel = () => {
    setFormData(profile);
    setIsEditing(false);
  };

  if (loading) {
    return (
      <div className="center-txt">
        <md-circular-progress indeterminate></md-circular-progress>
        Loading...
      </div>
    )
  }

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
        <h2>Personal information</h2>
        {!isEditing ? (
          <div>
            <p><strong>Email:</strong> {profile.email}</p>
            <p><strong>First name:</strong> {profile.first_name || ''}</p>
            <p><strong>Family name:</strong> {profile.family_name || ''}</p>
            <p><strong>City:</strong> {profile.address?.city || ''}</p>
            <p><strong>Country:</strong> {profile.address?.country || ''}</p>
          </div>
        ) : (
          <div className="flex-column">
            <md-outlined-text-field
              label="Email"
              value={formData.email}
              disabled
            />
            <md-outlined-text-field
              label="First name"
              name="first_name"
              value={formData.first_name || ''}
              onChange={handleChange}
              required
            />
            <md-outlined-text-field
              label="Family name"
              name="family_name"
              value={formData.family_name || ''}
              onChange={handleChange}
              required
            />
            <md-outlined-text-field
              label="City"
              name="address.city"
              value={formData.address.city || ''}
              onChange={handleChange}
            />
            <md-outlined-text-field
              label="Country"
              name="address.country"
              value={formData.address.country || ''}
              onChange={handleChange}
            />
          </div>
        )}
      </div>
      <div className="content">
        <h2>Notification preferences</h2>
        <div className="label">
          {!isEditing ? (
            <md-checkbox
              name="email_permission"
              checked={profile.email_permission}
              disabled
            />
          ) : (
            <md-checkbox
              name="email_permission"
              checked={formData.email_permission}
              onChange={handleCheck}
            />
          )}
          <label>Email</label>
        </div>
      </div>
      <div className="content">
        <div className="label">
          {!isEditing ? (
            <md-checkbox
              name="allowShareName"
              checked={profile.allowShareName}
              disabled
            />
          ) : (
            <md-checkbox
              name="allowShareName"
              checked={profile.allowShareName}
              onChange={handleCheck}
            />
          )}
          <label>Allow sharing of my name on leaderboard</label>
        </div>
      </div>
      {!isEditing ? (
        <md-filled-button className="btn-left" onClick={() => { setIsEditing(true); setFormData(profile) }}>
          Edit
          <md-icon slot="icon">edit</md-icon>
        </md-filled-button>
      ) : (
        <div>
          <md-outlined-button className="btn-left" onClick={handleCancel} disabled={saving}>
            Cancel
            <md-icon slot="icon">cancel</md-icon>
          </md-outlined-button>
          {!saving ? (
            <md-filled-button className="btn-right" onClick={handleSave}>
              Save
              <md-icon slot="icon">check_circle</md-icon>
            </md-filled-button>
          ) : (
            <div className="btn-right">
              <md-circular-progress indeterminate></md-circular-progress>
              Saving...
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Profile() {
  return (
    <div>
      <Header />
      <main>
        <h2>Profile page</h2>
        <PersonalInfo />
      </main>
    </div>
  );
};

export default Profile;