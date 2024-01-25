export function deleteSensor(): void {
  // Perform the delete action, e.g., show a confirmation dialog
  if (confirm("Are you sure you want to delete this sensor?")) {
    // Delete the sensor
    fetch(window.location.href, {
      method: "DELETE",
    }).then(function (response) {
      if (response.ok) {
        // If the sensor was deleted successfully, close the popup window
        window.close();
      } else {
        // If the sensor was not deleted successfully, show an alert
        alert("Sensor not deleted");
      }
    });
  } else {
    // Do nothing
    alert("Sensor not deleted");
  }
}

export function editSensor(event: Event): void {
  event.preventDefault(); // prevent the form from submitting normally

  const form = event.target as HTMLFormElement;
  const url = form.action; // get the form's action URL
  const formData = new FormData(form); // get the form data

  // send the form data to the server
  fetch(url, {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      } else {
        window.close();
      }
    })
    .catch((error) => {
      // handle error - don't close the window if there was an error
      console.error("Error:", error);
    });
}

declare global {
  interface Window {
    deleteSensor: () => void;
    editSensor: (event: Event) => void;
  }
}

window.deleteSensor = deleteSensor;
window.editSensor = editSensor;
