import React, { useState,useEffect} from 'react'
import axios from 'axios';
const Records = () => {
    const [input, setInput] = useState('');
    const [reports, setReports] = useState([]);
    const [initialReports, setInitialReports] = useState([]);
    const [fetchFiltered, setFetchFiltered] = useState(false);
    const [isChecked, setIsChecked] = useState(false);
    const[patientNames,setPatientNames]=useState([]);

    useEffect(() => {
        // Fetch the list of reports from the backend
        const fetchReports = async () => {
        try {
            const response = await axios.get('http://192.168.29.28:8000/reports_all');
            setReports(response.data.reports);
            setInitialReports(response.data.reports);
        } catch (error) {
            console.error('Error fetching reports:', error);
        }
        };

        fetchReports();
    }, []);
      // Fetch filtered reports when input changes or when the Enter key is pressed
    useEffect(() => {
      const fetchFilteredReports = async () => {
          try {
              console.log('input',input)
              console.log('fetch reports triggered')
              const response = await axios.post('http://192.168.29.28:8000/filter_reports', { 'text': input ,'isInvestigation': isChecked});
              const result = response.data;
              // console.log('result',result)
              setReports(result.reports); // Update reports based on filtering
              setPatientNames(response.data.patient_names);
              console.log(result.patient_names)
          } catch (error) {
              console.error('Error fetching filtered reports:', error);
          }
      };

      if (fetchFiltered || isChecked !== null) {
          fetchFilteredReports();
          setFetchFiltered(false); // Reset the state
      }

      // if(isChecked){
      //   fetchFilteredReports();
      // }
  }, [fetchFiltered, input,isChecked]);

//   useEffect(() => {
//     // Fetch filtered reports when isChecked changes
//     const fetchFilteredReports = async () => {
//         try {
//           console.log('fetch reports triggered isChecked')
//           console.log('isChecked',isChecked)
//             const response = await axios.post('http://192.168.29.28:8000/filter_reports', { 'text': input, 'isInvestigation': isChecked });
//             setReports(response.data.reports); // Update reports based on filtering
//         } catch (error) {
//             console.error('Error fetching filtered reports:', error);
//         }
//     };

//     fetchFilteredReports();
// }, [isChecked]); // Trigger when isChecked changes

    const handleReportClick = (reportName) => {
        // Open the PDF file in a new tab
        window.open(`http://192.168.29.28:8000/reports/${reportName}`, '_blank');
      };
    
      const handleInputEnterPress = () => {
        if (input.trim()) {
            setFetchFiltered(true); // Set state to trigger fetching filtered reports
        } else {
            // Reset reports to initial reports when input is cleared
            setReports(initialReports);
        }
    };

    const handleCheckboxChange = (event) => {
      const newValue = event.target.checked;
      setIsChecked(newValue);
      console.log('isChecked', newValue);
    };

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
        placeholder="What are you looking for.."
        className="w-full p-2 pr-10 text-black rounded-lg overflow-y-auto"
      />
      </div>
      <div className="flex items-center mb-6">
      <input
        id="default-checkbox"
        type="checkbox"
        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
        checked={isChecked}
        onChange={handleCheckboxChange}
      />
      <label
        htmlFor="default-checkbox"
        className="ms-2 text-sm font-medium text-white dark:text-gray-300"
      >
        Investigations only
      </label>
</div>
      <div className="w-3/4 p-6 bg-gray-800 rounded-lg overflow-y-auto max-h-96">
        <div className="grid grid-cols-3 gap-4">
          {reports.map((report, index) => {
            const patientId = report.split('_')[0]; 
            const reportTypechunk = report.split('_')[1]; 
            const reportType=reportTypechunk.split('.')[0];
            return(
            
            <div
              key={index}
              className="p-3 py-10 px-6 bg-gray-700 shadow rounded-lg cursor-pointer"
              onClick={() => handleReportClick(report)}
            >
              {/* {reportType.charAt(0).toUpperCase()+reportType.slice(1)} id: {patientId} */}
              {patientNames[index]}, {reportType.charAt(0).toUpperCase()+reportType.slice(1)} id: {patientId}
            </div>
          )})}
        </div>
      </div>
    </div>
  )
}

export default Records
