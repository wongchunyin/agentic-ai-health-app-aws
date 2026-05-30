import Header from '../components/Header.jsx';
import Score from '../components/Score.jsx';
import Plans from '../components/Plans.jsx';

function HomePage() {
  return (
    <div>
      <Header />
      <main>
        <h2>Welcome!</h2>
        <Score />
        <h2>Plans</h2>
        <Plans />
      </main>
    </div>
  );
}

export default HomePage;
