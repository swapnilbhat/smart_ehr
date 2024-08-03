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
        <h1 className="text-2xl font-bold">Your Reports</h1>
      </div>
     <ul className="flex flex-col space-y-2 mt-4">
        {reports.map((report, index) => (
          <li key={index}>
            <a
              href={`http://localhost:8000/reports/${report}`}
              download
              className="block p-2 bg-gray-700 hover:bg-gray-600 rounded"
            >
              {report}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
  // return (
  //   <div className="w-64 bg-gray-800 p-4 flex flex-col h-screen fixed overflow-y-auto">
  //     <div className="flex-shrink-0 mb-4">
  //       <h1 className="text-2xl font-bold">Your Reports</h1>
  //     </div>
  //    <ul className="flex flex-col space-y-2">
  //       {reports.map((report, index) => (
  //         <li key={index}>
  //           <a
  //             href={`http://localhost:8000/reports/${report}`}
  //             download
  //             className="block p-2 bg-gray-700 hover:bg-gray-600 rounded"
  //           >
  //             {report}
  //           </a>
  //         </li>
  //       ))}
  //     </ul>
  //   </div>
  // );
};

export default Sidebar;
