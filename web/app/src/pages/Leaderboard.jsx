import { useState, useEffect } from "react";
import Header from '../components/Header.jsx';
import '@material/web/icon/icon.js';

function Rankings() {
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		const getRankings = async () => {
			try {
				const response = await fetch('https://7xhw2qub6l.execute-api.us-east-1.amazonaws.com/prod/leaderboard', {
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
				sessionStorage.setItem("leaderboard", JSON.stringify(result.leaderboard));

			} catch (e) {
				console.error(e.message);
			}

			setLoading(false);
		}

		getRankings();
	}, []);

	if (loading) {
		return (
			<div className="center-txt">
				<md-circular-progress indeterminate></md-circular-progress>
				Loading...
			</div>
		)
	}

	const items = JSON.parse(sessionStorage.getItem("leaderboard"));

	if (items && items.length > 0) {
		return (
			<div>
				<div className="plan-list">
					{items.slice(0, 99).map((item, index) => (
						<div key={index} className="plan">
							<div className="plan-header">
								<h2>#{index + 1}</h2>
								<div className="center-txt">
									<h3>{item.username}</h3>
									{item.country && <p>{item.country}</p>}
									{item.city && <p>{item.city}</p>}
								</div>
								<div className="plan-header">
									<h2>{item.score}</h2>
									<md-icon>trophy</md-icon>
								</div>
							</div>
						</div>
					))}
				</div>
			</div>
		);
	} else {
		return (
			<div className="prompt">
				<p>No leaderboard data available.</p>
			</div>
		);
	}
}

function Leaderboard() {
	return (
		<div>
			<Header />
			<main>
				<h2>Leaderboard</h2>
				<Rankings />
			</main>
		</div>
	);
}

export default Leaderboard;