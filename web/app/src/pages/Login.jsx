import '@material/web/button/elevated-button.js';

const Login = () => {
  const handleLogin = () => {
    // const awsLoginUrl = "https://livewell.auth.us-east-1.amazoncognito.com/login?client_id=2n6ggumluvpk831jkl2a119rl1&response_type=code&scope=email+openid+phone&redirect_uri=https%3A%2F%2Fd3jkj7lzcnesij.cloudfront.net%2Fcallback";
    const awsLoginUrl = "https://livewell.auth.us-east-1.amazoncognito.com/login/continue?client_id=2n6ggumluvpk831jkl2a119rl1&redirect_uri=http%3A%2F%2Flocalhost%3A5173%2Fcallback&response_type=code&scope=email+openid+phone";
    window.location.href = awsLoginUrl;
  };

  return (
      <div className="login">
        <div className="logo-white">
            <img src="/logo/logo.png" width="200" height="100" />
        </div>
        <h1>Welcome to LiveWell!</h1>
        <h2>An AI companion for healthy ageing</h2>
        <md-elevated-button className="login-btn" onClick={handleLogin}>
          Log in
        </md-elevated-button>
      </div>
  );
};

export default Login;