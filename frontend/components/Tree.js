import { useState } from "react";

function Node({ node, selected, setSelected }) {
  const isChecked = selected.includes(node.id);

  const toggle = () => {
    if (isChecked) {
      setSelected(selected.filter((id) => id !== node.id));
    } else {
      setSelected([...selected, node.id]);
    }
  };

  return (
    <div style={{ marginLeft: 20 }}>
      <label>
        <input type="checkbox" checked={isChecked} onChange={toggle} />
        {node.name}
      </label>

      {node.children?.map((child) => (
        <Node
          key={child.id}
          node={child}
          selected={selected}
          setSelected={setSelected}
        />
      ))}
    </div>
  );
}

export default function Tree({ data, selected, setSelected }) {
  return (
    <div>
      {Array.isArray(data)
        ? data.map((n) => (
            <Node
              key={n.id}
              node={n}
              selected={selected}
              setSelected={setSelected}
            />
          ))
        : data && (
            <Node
              node={data}
              selected={selected}
              setSelected={setSelected}
            />
          )}
    </div>
  );
}