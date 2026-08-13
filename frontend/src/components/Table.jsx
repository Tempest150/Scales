import * as React from 'react';
/* import Table from '../components/Table';

const columns = [
  { label: 'Company', property: 'company' },              // plain text, read-only by default
  { label: 'Role', property: 'role_title' },
  {
    label: 'Status',
    property: 'status',
    type: 'select',                                        // only used when editable=true
    options: ['applied', 'oa', 'interview', 'rejected', 'offer', 'ghosted'],
  },
  {
    label: 'Updated',
    property: 'status_changed_at',
    type: 'date',
    format: (d) => new Date(d).toLocaleDateString(),        // used when editable=false
  },
];

const rows = applications.map((a) => ({ id: a.id, ...a })); // every row needs an `id`

// plain, read-only
<Table columns={columns} nodes={rows} />

// searchable only (filters on columns[0].property by default)
<Table columns={columns} nodes={rows} searchable searchProperty="company" />

// editable only (inline inputs per column `type`)
<Table columns={columns} nodes={rows} editable />

// both combined
<Table columns={columns} nodes={rows} searchable editable />
 */
import { CompactTable } from '@table-library/react-table-library/compact';
import { useTheme } from '@table-library/react-table-library/theme';
import { DEFAULT_OPTIONS, getTheme } from '@table-library/react-table-library/material-ui';

const cellInputStyle = { width: '100%', border: 'none', fontSize: '1rem', padding: 0, margin: 0 };

const formatValue = (value, column) => {
  if (column.format) return column.format(value);
  if (value instanceof Date) {
    return value.toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' });
  }
  if (typeof value === 'boolean') return value.toString();
  return value;
};

const renderEditableCell = (item, column, onUpdate) => {
  const value = item[column.property];

  switch (column.type) {
    case 'date':
      return (
        <input
          type="date"
          style={cellInputStyle}
          value={value instanceof Date ? value.toISOString().substring(0, 10) : ''}
          onChange={(event) => onUpdate(new Date(event.target.value), item.id, column.property)}
        />
      );
    case 'select':
      return (
        <select
          style={cellInputStyle}
          value={value}
          onChange={(event) => onUpdate(event.target.value, item.id, column.property)}
        >
          {(column.options || []).map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      );
    case 'checkbox':
      return (
        <input
          type="checkbox"
          checked={!!value}
          onChange={(event) => onUpdate(event.target.checked, item.id, column.property)}
        />
      );
    case 'number':
      return (
        <input
          type="number"
          style={cellInputStyle}
          value={value}
          onChange={(event) => onUpdate(Number(event.target.value), item.id, column.property)}
        />
      );
    default:
      return (
        <input
          type="text"
          style={cellInputStyle}
          value={value}
          onChange={(event) => onUpdate(event.target.value, item.id, column.property)}
        />
      );
  }
};

/**
 * columns: [{ label, property, type?: 'text'|'date'|'select'|'checkbox'|'number', options?, format? }]
 * searchable/editable both default false, i.e. a plain read-only table.
 */
const Table = ({ columns, nodes, searchable = false, editable = false, searchProperty }) => {
  const [data, setData] = React.useState({ nodes });
  const [search, setSearch] = React.useState('');

  // Reset local (editable) copy when the incoming `nodes` prop changes identity.
  // Done during render, not in an effect, to avoid a cascading extra render.
  const [prevNodes, setPrevNodes] = React.useState(nodes);
  if (nodes !== prevNodes) {
    setPrevNodes(nodes);
    setData({ nodes });
  }

  const handleUpdate = (value, id, property) => {
    setData((state) => ({
      ...state,
      nodes: state.nodes.map((node) => (node.id === id ? { ...node, [property]: value } : node)),
    }));
  };

  const theme = useTheme(getTheme(DEFAULT_OPTIONS));

  const filterProperty = searchProperty || columns[0].property;
  const visibleNodes = searchable
    ? data.nodes.filter((node) =>
        String(node[filterProperty] ?? '')
          .toLowerCase()
          .includes(search.toLowerCase()),
      )
    : data.nodes;

  const tableColumns = columns.map((column) => ({
    label: column.label,
    renderCell: (item) =>
      editable
        ? renderEditableCell(item, column, handleUpdate)
        : formatValue(item[column.property], column),
  }));

  return (
    <>
      {searchable && (
        <input
          type="text"
          placeholder={`Search ${columns.find((c) => c.property === filterProperty)?.label || ''}`}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          style={{ marginBottom: '0.5rem', padding: '0.5rem', width: '100%', boxSizing: 'border-box' }}
        />
      )}

      <CompactTable columns={tableColumns} data={{ nodes: visibleNodes }} theme={theme} />
    </>
  );
};

export default Table;
