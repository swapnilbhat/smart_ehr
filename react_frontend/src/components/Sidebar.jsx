import React, { useState,useEffect } from "react";
import axios from 'axios';
const Sidebar = ({refreshReports}) => {
  const [reports, setReports] = useState([]);
  const fetchReports = async () => {
    try {
      const response = await axios.get('http://localhost:8000/reports');
      setReports(response.data.reports);
    } catch (error) {
      console.error('Error fetching reports:', error);
    }
  };
  useEffect(() => {
    fetchReports();
  }, [refreshReports]);

  return (
    <div className="w-64 bg-gray-800 p-4 flex flex-col">
      <div className="flex-shrink-0">
        <h1 className="text-2xl font-bold mt-4">Recent Records</h1>
      </div>
     <ul className="flex flex-col space-y-2 mt-4">
        {reports.map((report, index) => {
          const patientId = report.split('_')[0]; 
          const reportTypechunk = report.split('_')[1]; 
          const reportType=reportTypechunk.split('.')[0];
          return(
          <li key={index}>
            <a
              href={`http://localhost:8000/reports/${report}`}
              download
              className="block p-2 bg-gray-700 hover:bg-gray-600 rounded"
            >
             {reportType.charAt(0).toUpperCase()+reportType.slice(1)} id: {patientId}
            </a>
          </li>
        )})}
      </ul>
    </div>
  );
};

export default Sidebar;
