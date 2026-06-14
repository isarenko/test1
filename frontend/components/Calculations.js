import { useEffect, useState } from "react";

export default function Calculations() {
  const [calculations, setCalculations] = useState([]);
  const [loading, setLoading] = useState(true);

  const API = "http://localhost:8000";

  const loadCalculations = async () => {
    try {
      const res = await fetch(`${API}/calculations`);
      const data = await res.json();
      setCalculations(data);
    } catch (e) {
      console.error("Error loading calculations:", e);
    } finally {
      setLoading(false);
    }
  };

  const downloadExcel = async (calc_id) => {
    const res = await fetch(`${API}/export/${calc_id}`);
    const blob = await res.blob();

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");

    a.href = url;
    a.download = "result.xlsx";
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const loadOne = async (calc_id) => {
    const res = await fetch(`${API}/calculations/${calc_id}`);
    const data = await res.json();

    alert("Loaded calculation:\n" + JSON.stringify(data, null, 2));
  };

  useEffect(() => {
    loadCalculations();
  }, []);

  return (
    <div style={{ padding: 20 }}>
      <h1>Saved calculations</h1>

      {loading && <p>Loading...</p>}

      {calculations.map((c) => (
        <div
          key={c.calc_id}
          style={{
            border: "1px solid #ccc",
            marginBottom: 10,
            padding: 10,
          }}
        >
          <p><b>ID:</b> {c.calc_id}</p>
          <p><b>Session:</b> {c.session_id}</p>
          <p><b>Status:</b> {c.status}</p>

          <button onClick={() => loadOne(c.calc_id)}>
            Open JSON
          </button>

          <button onClick={() => downloadExcel(c.calc_id)}>
            Download Excel
          </button>
        </div>
      ))}
    </div>
  );
}