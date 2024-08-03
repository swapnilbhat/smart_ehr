import React,{useState} from "react";
import Navbar from "./components/Navbar";
import Information from "./components/Information";
import Chatbar from "./components/Chatbar";
import Sidebar from "./components/Sidebar";

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
    <div className="flex h-screen bg-gray-900 text-white">
      <Sidebar refreshReports={refreshReports} />
      <div className="flex-1">
        <Navbar />
          <Information messages={messages} />
        <Chatbar onSendMessage={handleSendMessage} onReportCreated={handleRefreshReports} />
      </div>
    </div>
  );
  // return (
  //   <div className="flex h-screen bg-gray-900 text-white">
  //     <Sidebar refreshReports={refreshReports} />
  //     <div className="flex-1 flex flex-col ml-64">
  //       <Navbar />
  //       <div className="flex-1 flex overflow-hidden">
  //         <Information messages={messages} />
  //         </div>
  //       <Chatbar onSendMessage={handleSendMessage} onReportCreated={handleRefreshReports} />
  //     </div>
  //   </div>
  // );
}
export default App;

