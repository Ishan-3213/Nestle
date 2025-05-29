import Chatbot from "./components/ChatBot";

function App() {
  return (
    <div
  className="app"
  style={{
    backgroundImage: "url('NestleBG.jpg')",
    backgroundSize: "cover",
    backgroundPosition: "left center",
    height: "100vh",
    width: "93vw"
  }}
>
  <Chatbot />
</div>

  );
}

export default App;
