import React, { useState,useEffect} from 'react'
import axios from 'axios';
const Records = () => {
    const [input, setInput] = useState('');
    const [reports, setReports] = useState([]);

    useEffect(() => {
        // Fetch the list of reports from the backend
        const fetchReports = async () => {
        try {
            const response = await axios.get('http://localhost:8000/reports_all');
            setReports(response.data.reports);
        } catch (error) {
            console.error('Error fetching reports:', error);
        }
        };

        fetchReports();
    }, []);

    const handleReportClick = (reportName) => {
        // Open the PDF file in a new tab
        window.open(`http://localhost:8000/reports/${reportName}`, '_blank');
      };
    
    const handleInputEnterPress=async ()=>{
        if(input.trim()){
            try {
            console.log(input)
            const response = await axios.post('http://localhost:8000/filter_reports', { 'text': input });
            const result=response.data
            console.log(result.output)
        }
        catch(error){
            console.error('Error fetching filtered reports:', error);
        }
        }
    }

  return (
    <div className='flex flex-col items-center justify-center mt-2'>
      <div className="w-1/2 p-4 mt-12 mb-3">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
            if (e.key === 'Enter') {
              handleInputEnterPress(e.target.value);
            }
          }}
        placeholder="What are you looking for"
        className="w-full p-2 pr-10 text-black rounded-lg overflow-y-auto"
      />
      </div>
      <div className="w-3/4 p-6 bg-gray-800 rounded-lg overflow-y-auto max-h-96">
        <div className="grid grid-cols-4 gap-4">
          {reports.map((report, index) => {
            const patientId = report.split('_')[0]; 
            return(
            
            <div
              key={index}
              className="p-4 bg-gray-700 shadow rounded-lg cursor-pointer"
              onClick={() => handleReportClick(report)}
            >
              Patient Id: {patientId}
            </div>
          )})}
        </div>
      </div>
    </div>
  )
}

export default Records
