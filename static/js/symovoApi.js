const apiUrl = "http://192.168.178.59/api/v0/amr";

async function fetchRobotIds() {
  try {
    const response = await fetch(apiUrl);
    if (response.ok) {
      const robots = await response.json();
      console.log("Available Robots:", robots);
      robots.forEach(robot => {
        console.log(`Robot ID: ${robot.id}, Name: ${robot.name}`);
      });
    } else {
      console.error("Failed to fetch robots.");
    }
  } catch (err) {
    console.error("Error:", err);
  }
}

fetchRobotIds();
