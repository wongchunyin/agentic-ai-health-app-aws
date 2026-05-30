import { useState, useEffect } from "react";
import Header from '../components/Header.jsx';
import AssessmentForm from '../components/AssessmentForm.jsx';

function GetAssessment() {
  const [assessmentType, setAssessmentType] = useState("FRAIL");

  const params = new URLSearchParams(location.search);
  const assessment_type = params.get('assessment_type');

  const handleChange = (e) => {
    setAssessmentType(e.target.value);
  };

  const handleUpdate = () => {
    window.location.href = `/assessment?assessment_type=${assessmentType}`;
  }

  if (assessment_type) {
    return <AssessmentForm />;
  }

  return (
    <div className="prompt">
      <p>Select an assessment type:</p>
      <md-outlined-select label="Type" value={assessmentType} onChange={handleChange}>
        <md-select-option value="FRAIL">FRAIL</md-select-option>
        <md-select-option value="ROCKWOOD_MITNITSKI">Rockwood Mitnitski</md-select-option>
      </md-outlined-select>
      <md-filled-button className="btn-center" onClick={handleUpdate}>Start</md-filled-button>
      <p className="center-txt"><b>FRAIL: </b>(Fatigue, Resistance, Ambulance, Illnesses, Loss of weight) A relatively short questionnaire of 5 questions to quickly get a frailty assessment.</p>
      <p className="center-txt"><b>Rockwood Mitnitski: </b>A longer survey involving 40 questions to get a more detailed assessment of frailty.</p>
    </div>
  );
}

function Assessment() {
  return (
    <div>
      <Header />
      <main>
        <h2>Assessment</h2>
        <GetAssessment />
      </main>
    </div>
  );
}

export default Assessment;