<script>
  import { onMount } from "svelte";

  let message = "";
  let loading = false;
  let error = null;
  let showCreateUpload = false;
  let showDeleteHistory = false;
  let flightHistory = {};
  let flightstats = {};

  // Lets
  let depQuery = ""; // Departure airport query
  let arrQuery = ""; // Arrival airport query
  let depicaos = [];
  let arricaos = [];
  let timeout;
  let selectedDepIcao = "";
  let selectedArrIcao = "";
  let selectedDate = "";
  let all_selected = true;
  let doublesubmission = null;

  let file = null; // To store the selected file

  // This function is called when the file is selected
  const onFileChange = async (event) => {
    file = event.target.files[0]; // Get the selected file
    if (file) {
      await uploadFile(); // Automatically upload the file after selection
    }
  };

  // Function to handle the file upload
  const uploadFile = async () => {
    if (!file) {
      return; // If no file is selected, return early
    }

    // Create a FormData object to send the file
    const formData = new FormData();
    formData.append("file", file); // Append the file to FormData object

    try {
      const response = await fetch("http://localhost:8000/history", {
        method: "PUT", // Use PUT method to upload the file
        body: formData, // Attach the file in the request body
        credentials: "include", // Ensure cookies are included
      });

      if (!response.ok) {
        console.error("Failed to upload the file");
      }
      fetchHistoryList();
    } catch (error) {
      console.error("Error:", error);
    }
  };

  // Function to trigger file input when the link is clicked
  const triggerFileInput = () => {
    document.getElementById("fileInput").click(); // Trigger file input click
  };

  // Fetch flight history
  async function fetchHistoryList() {
    loading = true;
    try {
      const response = await fetch("http://localhost:8000/flight", {
        method: "GET", // Use GET instead of POST
        credentials: "include",
      });
      if (response.status === 400) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || "Bad Request: Something went wrong"
        );
      }
      const data = await response.json();
      flightHistory = data;
      fetchEmissionHistory();
      showCreateUpload = false;
      showDeleteHistory = true;
      error = null;
    } catch (err) {
      error = err.message;
      showCreateUpload = true;
    } finally {
      loading = false;
    }
  }

  // Fetch flight history
  async function fetchEmissionHistory() {
    loading = true;
    try {
      const response = await fetch("http://localhost:8000/stats", {
        method: "GET", // Use GET instead of POST
        credentials: "include",
      });
      if (response.status === 400) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || "Bad Request: Something went wrong"
        );
      }
      const data = await response.json();
      flightstats = data;
    } catch (err) {
      error = err.message;
      showCreateUpload = true;
    } finally {
      loading = false;
    }
  }

  // Create a history
  async function createHistory() {
    try {
      const response = await fetch("http://localhost:8000/history", {
        method: "POST", // POST request
        headers: {
          "Content-Type": "application/json", // Ensure the correct content type
        },
        credentials: "include",
      });
      fetchHistoryList();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  // Delete history
  async function deleteHistory() {
    try {
      const response = await fetch("http://localhost:8000/history", {
        method: "DELETE",
        credentials: "include",
      });
      showDeleteHistory = false;
      fetchHistoryList();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  // Function to trigger the download of the flight history
  async function downloadHistory() {
    try {
      // Fetch the flight history from the FastAPI endpoint
      const response = await fetch("http://localhost:8000/history", {
        method: "GET",
        credentials: "include",
      });

      // Check if the response is successful (status code 200)
      if (!response.ok) {
        throw new Error("Failed to download the file");
      }

      // Convert the response into a Blob (binary large object)
      const blob = await response.blob();

      // Create a download link for the file
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "flight_history.json"; // Specify the file name for download
      document.body.appendChild(a);
      a.click(); // Trigger the download
      document.body.removeChild(a); // Clean up by removing the link element
    } catch (error) {
      console.error("Error during download:", error);
    }
  }

  // Fetch search results from FastAPI backend
  async function fetchSuggestions(query, isDeparture) {
    if (query.length > 2) {
      try {
        const response = await fetch(
          `http://127.0.0.1:8000/airport?query=${query}`
        );
        const data = await response.json();
        if (isDeparture) {
          depicaos = data.icaos;
        } else {
          arricaos = data.icaos;
        }
      } catch (error) {
        console.error("Error fetching icaos:", error);
      }
    }
  }

  // Debounce input to avoid excessive API calls
  function handleInput(event, isDeparture) {
    const queryValue = event.target.value;
    if (isDeparture) {
      depQuery = queryValue;
    } else {
      arrQuery = queryValue;
    }
    clearTimeout(timeout);
    timeout = setTimeout(() => fetchSuggestions(queryValue, isDeparture), 300); // Wait for 300ms before sending the request
  }

  // Select an ICAO from the list
  function selectIcao(icao, isDeparture) {
    if (isDeparture) {
      selectedDepIcao = icao;
      depQuery = icao; // Update input field for departure
    } else {
      selectedArrIcao = icao;
      arrQuery = icao; // Update input field for arrival
    }
    if (isDeparture) {
      depicaos = [];
    } else {
      arricaos = [];
    } // Clear suggestions list
  }

  // Check if  everything is provided
  function allselected() {
    if (
      selectedDepIcao.length > 0 &&
      selectedArrIcao.length > 0 &&
      selectedDate.length > 0
    )
      all_selected = false;
  }

  // Send selected ICAOs to FastAPI endpoint when the button is clicked
  async function submitSelection() {
    if (selectedDepIcao && selectedArrIcao && selectedDate) {
      try {
        const response = await fetch(
          `http://localhost:8000/flight?departure=${selectedDepIcao}&arrival=${selectedArrIcao}&date=${selectedDate}`,
          {
            method: "POST", // POST request
            headers: {
              "Content-Type": "application/json", // Ensure the correct content type
            },
            credentials: "include",
          }
        );
        const data = await response.json();
        if (response.status === 409) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || "Bad Request: Something went wrong"
          );
        }
        fetchHistoryList();
        console.log("Selection submitted successfully:", data);
        doublesubmission = null;
      } catch (err) {
        console.error("Error submitting selection:", err);
        doublesubmission = err.message;
      }
    } else {
      console.log("Both ICAO selections are required");
    }
  }

  // Fetch the data when the component is mounted
  onMount(() => {
    fetchHistoryList();
  });
</script>

<!-- Svelte Component HTML -->

{#if showCreateUpload}
  <div>
    <button on:click={createHistory} disabled={loading}>
      Create New Flight History
    </button>

    <div class="read-the-docs">
      <!-- Hidden file input element -->
      <input
        id="fileInput"
        type="file"
        accept=".json"
        on:change={onFileChange}
        style="display: none;"
      />

      <!-- Single link to trigger file input and upload -->
      Or click
      <a href="#" on:click|preventDefault={triggerFileInput} class="upload-link"
        >here</a
      > to upload an exisitng flight history.
    </div>
  </div>
{/if}

<div>
  {#if loading}
    <div class="loading">Loading...</div>
  {:else if error}
    <div class="error">{error}</div>
  {:else}
    <!-- <button on:click={() => getModal().open()}> Add new flight </button> -->

    <!-- the modal without an `id` -->
    <!-- <Modal> -->

    <div class="inputs-container">
      <b>Add a new flight:</b>
      <!-- Departure Airport -->
      <div class="input-wrapper">
        <input
          type="text"
          placeholder="Departure Airport"
          bind:value={depQuery}
          on:input={(event) => handleInput(event, true)}
          aria-label="Departure Airport"
        />
        <div class="autocomplete-icaos">
          {#each Object.keys(depicaos) as icao}
            <div
              class="autocomplete-item"
              on:click={() => selectIcao(icao, true)}
            >
              {icao} [{depicaos[icao]["iata"]} - {depicaos[icao]["matched"]}]
            </div>
          {/each}
        </div>
      </div>

      {error}
      <!-- Arrival Airport -->
      <div class="input-wrapper">
        <input
          type="text"
          placeholder="Arrival Airport"
          bind:value={arrQuery}
          on:input={(event) => handleInput(event, false)}
          aria-label="Arrival Airport"
        />
        <div class="autocomplete-icaos">
          {#each Object.keys(arricaos) as icao}
            <div
              class="autocomplete-item"
              on:click={() => selectIcao(icao, false)}
            >
              {icao} [{arricaos[icao]["iata"]} - {arricaos[icao]["matched"]}]
            </div>
          {/each}
        </div>
      </div>

      <!-- Depature Date -->
      <div class="input-wrapper">
        <input
          type="date"
          id="date-input"
          placeholder="Arrival Airport"
          bind:value={selectedDate}
          on:input={allselected}
          aria-label="Date input"
        />
      </div>

      <button on:click={submitSelection} disabled={all_selected}> Add </button>
    </div>
    {#if doublesubmission}
      <div class="error">Already submitted this flight</div>
    {/if}
    <!-- </Modal> -->
    <div class="inputs-container">
      So far you have produced
      <b>{flightstats["Total CO2 [kg]"]}</b> CO2 kg flying
      <b>{flightstats["Number of flights"]}</b> times over
      <b>{flightstats["Total Distance [km]"]}</b> km.
    </div>
    {#each Object.keys(flightHistory).reverse() as flightId}
      <div class="flight-box">
        <div class="flight-details">
          <div class="flight-master">
            <strong>🛫 Departure:</strong>&nbsp;
            {flightHistory[flightId]["DEPARTURE"]["name"]} [{flightHistory[
              flightId
            ]["DEPARTURE"]["iata"]}]|
            {flightHistory[flightId]["DEPARTURE"]["city"]} |
            {flightHistory[flightId]["DEPARTURE"]["country"]}
          </div>
        <div class="flight-master">→</div>
          <div class="flight-master">
            <strong>🛬 Arrival:</strong>&nbsp;
            {flightHistory[flightId]["ARRIVAL"]["name"]} [{flightHistory[
              flightId
            ]["ARRIVAL"]["iata"]}]|
            {flightHistory[flightId]["ARRIVAL"]["city"]} |
            {flightHistory[flightId]["ARRIVAL"]["country"]}
          </div>
        </div>
        <div class="flight-info">
          Date: {flightHistory[flightId]["INFO"]["Date"]} | CO2 [kg]: {flightHistory[
            flightId
          ]["INFO"]["CO2 [kg]"]} | Distance [km]: {flightHistory[flightId][
            "INFO"
          ]["Distance [km]"]} | Type: {flightHistory[flightId]["INFO"]["Type"]}
        </div>
      </div>
    {/each}
  {/if}
</div>

{#if showDeleteHistory}
  <div class="button-container">
    <div>
      <button on:click={deleteHistory}> Delete History </button>
    </div>
    <div>
      <button on:click={downloadHistory}> Download History </button>
    </div>
  </div>
{/if}


<style>
  
  .button-container {
    display: flex; /* Makes the buttons appear in a row */
    gap: 10px; /* Adds space between buttons */
    align-items: center; /* Center elements horizontally */
    justify-content: center;
    margin-top: 10px;
  }
  .read-the-docs {
    color: #888;
  }

  .loading {
    font-family: "Courier New", Courier, monospace; /* Code-like font */

    font-size: 16px;
    color: #007bff;
  }

  .error {
    font-family: "Courier New", Courier, monospace; /* Code-like font */

    font-size: 16px;
    color: red;
  }

  .flight-box {
    background-color: #f1f1f1; /* Light grey background */
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 10px;
  }

  .flight-master {
    display: flex;
    align-items: center; /* Center elements horizontally */
    justify-content: center; /* Optional: Ensure it's horizontally centered */
  }

  
  .flight-info {
    display: flex;
    align-items: left; /* Center elements horizontally */
    color: #888;
  }
  .flight-details {
    display: flex;
    justify-content: space-between; /* Align items horizontally */
    gap: 20px; /* Add spacing between each key-value pair */
  }

  .flight-details strong {
    display: inline; /* Ensure strong stays inline */
  }

  .autocomplete-icaos {
    border: 1px solid #ccc;
    max-height: 200px;
    overflow-y: auto;
    position: absolute;
    width: 100%;
    background-color: white;
    z-index: 10;
  }

  .autocomplete-item {
    padding: 8px;
    cursor: pointer;
  }

  .autocomplete-item:hover {
    background-color: #f0f0f0;
  }

  input {
    width: 100%;
    padding: 8px;
    border: 1px solid #ccc;
    box-sizing: border-box;
  }

  .inputs-container {
    display: flex;
    gap: 10px; /* Space between departure and arrival inputs */
    margin-bottom: 20px;
  }

  .input-wrapper {
    position: relative;
    flex: 1; /* Each input will take equal space */
  }
</style>
