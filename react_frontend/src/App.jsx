import React,{useState} from "react";
import Navbar from "./components/Navbar";
import Information from "./components/Information";
import Chatbar from "./components/Chatbar";
import Sidebar from "./components/Sidebar";
import Records from "./components/Records";
import { BrowserRouter as Router, Route,Routes } from "react-router-dom";

function App(){
  const [messages,setMessages]=useState([])
  const [refreshReports, setRefreshReports] = useState(false);

  const handleRefreshReports = () => {
    setRefreshReports((prev) => !prev);
  };

  const handleSendMessage=(message)=>{
    setMessages((prevMessages) => [...prevMessages, message]);
  }
  return (
    <Router>
      <Routes>
        <Route path='/' element={<div className="flex h-screen bg-gray-900 text-white">
        <Sidebar refreshReports={refreshReports} />
        <div className="flex-1">
          <Navbar />
            <Information messages={messages} />
          <Chatbar onSendMessage={handleSendMessage} onReportCreated={handleRefreshReports} />
        </div>
      </div>}/>
      <Route path='/records' element={<div className="flex h-screen bg-gray-900 text-white">
        <Sidebar refreshReports={refreshReports} />
        <div className="flex-1">
          <Navbar />
          <Records/>
        </div>
      </div>}/>
      </Routes>
  </Router>
    
  );
}
export default App;

