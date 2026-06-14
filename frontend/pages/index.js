import { useEffect, useState } from "react";
import {
  getTree,
  calculate,
  saveCalc,
  getCalculations,
  exportCalc,
  getCalc,
} from "../lib/api";

import Tree from "../components/Tree";

export default function Home() {
  const [tree, setTree] = useState([]);
  const [date, setDate] = useState("");
  const [selected, setSelected] = useState([]);
  const [amount, setAmount] = useState(1000);
  const [result, setResult] = useState(null);
  const [list, setList] = useState([]);

  useEffect(() => {
    loadTree();
    loadList();
  }, []);

  const loadTree = async (d) => {
    const res = await getTree(d);
    setTree(res.data);
  };

  const loadList = async () => {
    const res = await getCalculations();
    setList(res.data);
  };

  const handleCalculate = async () => {
    const res = await calculate({
      selected_ids: selected,
      amount: Number(amount),
    });

    setResult(res.data);
  };

  const handleSave = async () => {
    if (!result?.calc_id) return;
    await saveCalc(result.calc_id);
    loadList();
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>СПП система</h2>

      {/* DATE */}
      <input
        type="date"
        onChange={(e) => {
          setDate(e.target.value);
          loadTree(e.target.value);
        }}
      />

      {/* TREE */}
      <h3>Дерево</h3>
      <Tree data={tree} selected={selected} setSelected={setSelected} />

      {/* CALC */}
      <h3>Калькулятор</h3>
      <input
        type="number"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
      />

      <button onClick={handleCalculate}>Выполнить</button>

      {result && (
        <div>
          <h3>Результат</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>

          <button onClick={handleSave}>Сохранить</button>
        </div>
      )}

      {/* LIST */}
      <h3>Сохранённые расчёты</h3>

      {list.map((item) => (
        <div key={item.calc_id}>
          <div>
            {item.calc_id} | {item.status}
          </div>

          <button
            onClick={async () => {
              const res = await getCalc(item.calc_id);
              setResult(res.data);
            }}
          >
            Открыть
          </button>

          <a
            href={exportCalc(item.calc_id)}
            target="_blank"
            rel="noreferrer"
          >
            Скачать Excel
          </a>
        </div>
      ))}
    </div>
  );
}