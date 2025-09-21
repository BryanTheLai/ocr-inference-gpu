'use client';

import React, { useState, useMemo } from 'react';
import { ChevronDown, ChevronUp, Download, Filter, Search } from 'lucide-react';
import { downloadJSON, downloadCSV, cn } from '@/lib/utils';

interface DataTableProps {
  data: any[];
  onRowClick?: (row: any, index: number) => void;
  selectedRow?: number;
  title?: string;
}

export default function DataTable({ 
  data, 
  onRowClick, 
  selectedRow,
  title = "Extracted Data"
}: DataTableProps) {
  const [sortColumn, setSortColumn] = useState<string>('');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [filterText, setFilterText] = useState('');
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(new Set());

  const columns = useMemo(() => {
    if (!data || data.length === 0) return [];
    
    const allKeys = new Set<string>();
    data.forEach(row => {
      Object.keys(row).forEach(key => allKeys.add(key));
    });
    
    return Array.from(allKeys);
  }, [data]);

  const flattenObject = (obj: any, prefix = ''): any => {
    const flattened: any = {};
    
    Object.keys(obj).forEach(key => {
      const value = obj[key];
      const newKey = prefix ? `${prefix}.${key}` : key;
      
      if (value === null || value === undefined) {
        flattened[newKey] = '';
      } else if (typeof value === 'object' && !Array.isArray(value)) {
        Object.assign(flattened, flattenObject(value, newKey));
      } else if (Array.isArray(value)) {
        flattened[newKey] = value.map(item => 
          typeof item === 'object' ? JSON.stringify(item) : item
        ).join(', ');
      } else {
        flattened[newKey] = value;
      }
    });
    
    return flattened;
  };

  const processedData = useMemo(() => {
    return data.map(row => flattenObject(row));
  }, [data]);

  const filteredAndSortedData = useMemo(() => {
    let filtered = processedData;
    
    if (filterText) {
      filtered = filtered.filter(row => 
        Object.values(row).some(value => 
          String(value).toLowerCase().includes(filterText.toLowerCase())
        )
      );
    }
    
    if (sortColumn) {
      filtered = [...filtered].sort((a, b) => {
        const aVal = a[sortColumn];
        const bVal = b[sortColumn];
        
        if (aVal === bVal) return 0;
        
        const comparison = aVal < bVal ? -1 : 1;
        return sortDirection === 'asc' ? comparison : -comparison;
      });
    }
    
    return filtered;
  }, [processedData, filterText, sortColumn, sortDirection]);

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const toggleColumnVisibility = (column: string) => {
    const newVisible = new Set(visibleColumns);
    if (newVisible.has(column)) {
      newVisible.delete(column);
    } else {
      newVisible.add(column);
    }
    setVisibleColumns(newVisible);
  };

  const displayColumns = useMemo(() => {
    if (visibleColumns.size === 0) return columns;
    return columns.filter(col => visibleColumns.has(col));
  }, [columns, visibleColumns]);

  const exportData = (format: 'json' | 'csv') => {
    const exportData = filteredAndSortedData.length > 0 ? filteredAndSortedData : processedData;
    
    if (format === 'json') {
      downloadJSON(exportData, `${title.toLowerCase().replace(/\s+/g, '_')}_data.json`);
    } else {
      downloadCSV(exportData, `${title.toLowerCase().replace(/\s+/g, '_')}_data.csv`);
    }
  };

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
        <p className="text-gray-500">No data to display</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">{title}</h2>
        
        <div className="flex items-center space-x-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search..."
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          
          <div className="relative">
            <button
              className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
              onClick={() => {
                const menu = document.getElementById('column-menu');
                if (menu) {
                  menu.classList.toggle('hidden');
                }
              }}
            >
              <Filter className="w-4 h-4" />
              <span>Columns</span>
            </button>
            
            <div
              id="column-menu"
              className="hidden absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10"
            >
              <div className="p-2 max-h-64 overflow-y-auto">
                {columns.map(column => (
                  <label key={column} className="flex items-center space-x-2 p-2 hover:bg-gray-50 rounded cursor-pointer">
                    <input
                      type="checkbox"
                      checked={visibleColumns.size === 0 || visibleColumns.has(column)}
                      onChange={() => toggleColumnVisibility(column)}
                      className="rounded"
                    />
                    <span className="text-sm truncate">{column}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
          
          <button
            onClick={() => exportData('json')}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm"
          >
            <Download className="w-4 h-4" />
            <span>JSON</span>
          </button>
          
          <button
            onClick={() => exportData('csv')}
            className="flex items-center space-x-2 px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 text-sm"
          >
            <Download className="w-4 h-4" />
            <span>CSV</span>
          </button>
        </div>
      </div>

      <div className="overflow-x-auto border border-gray-200 rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {displayColumns.map(column => (
                <th
                  key={column}
                  onClick={() => handleSort(column)}
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  <div className="flex items-center space-x-1">
                    <span>{column}</span>
                    {sortColumn === column && (
                      sortDirection === 'asc' ? 
                        <ChevronUp className="w-4 h-4" /> : 
                        <ChevronDown className="w-4 h-4" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredAndSortedData.map((row, index) => (
              <tr
                key={index}
                onClick={() => onRowClick && onRowClick(row, index)}
                className={cn(
                  "hover:bg-gray-50 cursor-pointer transition-colors",
                  selectedRow === index && "bg-blue-50"
                )}
              >
                {displayColumns.map(column => (
                  <td key={column} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row[column] !== undefined && row[column] !== null ? (
                      typeof row[column] === 'boolean' ? (
                        <span className={cn(
                          "px-2 py-1 rounded-full text-xs font-medium",
                          row[column] ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                        )}>
                          {row[column] ? 'Yes' : 'No'}
                        </span>
                      ) : (
                        <span className="truncate block max-w-xs" title={String(row[column])}>
                          {String(row[column])}
                        </span>
                      )
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredAndSortedData.length === 0 && filterText && (
          <div className="text-center py-8">
            <p className="text-gray-500">No results found for "{filterText}"</p>
          </div>
        )}
      </div>
      
      <div className="mt-4 text-sm text-gray-600">
        Showing {filteredAndSortedData.length} of {processedData.length} rows
      </div>
    </div>
  );
}
