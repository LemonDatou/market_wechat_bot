package main

import (
 "bufio"
 "encoding/json"
 "fmt"
 "io/ioutil"
 "log"
 "net"
 "net/http"
 "os"
 "strings"
 "time"
)

const (
 WeChatMsgStartHook = 9
 WeChatMsgStopHook  = 10
 BaseURL            = "http://127.0.0.1:%d/api/?type=%d"
)

var callbackURL = os.Getenv("WECHAT_CALLBACK_URL")

func wechatHTTPAPI(api, port int, method string, data map[string]interface{}) (map[string]interface{}, error) {
 url := fmt.Sprintf(BaseURL, port, api)
 var resp *http.Response
 var err error

 if strings.ToLower(method) == "post" {
  jsonData, _ := json.Marshal(data)
  resp, err = http.Post(url, "application/json", strings.NewReader(string(jsonData)))
 } else {
  resp, err = http.Get(url)
 }

 if err != nil {
  return nil, err
 }
 defer resp.Body.Close()

 body, err := ioutil.ReadAll(resp.Body)
 if err != nil {
  return nil, err
 }

 var result map[string]interface{}
 err = json.Unmarshal(body, &result)
 return result, err
}

func sendCallback(msg map[string]interface{}) {
 if callbackURL == "" {
  log.Println("Callback URL not set. Skipping callback.")
  return
 }

 jsonData, err := json.Marshal(msg)
 if err != nil {
  log.Printf("Error marshaling message: %v", err)
  return
 }

 resp, err := http.Post(callbackURL, "application/json", strings.NewReader(string(jsonData)))
 if err != nil {
  log.Printf("Error sending message to callback URL: %v", err)
  return
 }
 defer resp.Body.Close()

 if resp.StatusCode == 200 {
//   log.Println("Message sent to callback URL successfully")
 } else {
  log.Printf("Failed to send message to callback URL. Status code: %d", resp.StatusCode)
 }
}

func handleConnection(conn net.Conn) {
 defer conn.Close()
 reader := bufio.NewReader(conn)

 for {
  message, err := reader.ReadString('\n')
  if err != nil {
//    log.Printf("Error reading from connection: %v", err)
   return
  }

  var msg map[string]interface{}
  err = json.Unmarshal([]byte(message), &msg)
  if err != nil {
   log.Printf("Failed to decode JSON message: %v", err)
   continue
  }

//   log.Printf("Received message: %v", msg)
  sendCallback(msg)

  _, err = conn.Write([]byte("200 OK\n"))
  if err != nil {
   log.Printf("Error sending response: %v", err)
   return
  }
 }
}

func startSocketServer(port int) error {
 listener, err := net.Listen("tcp", fmt.Sprintf("127.0.0.1:%d", port))
 if err != nil {
  return err
 }
 defer listener.Close()

 log.Printf("Starting server on port %d", port)

 for {
  conn, err := listener.Accept()
  if err != nil {
   log.Printf("Error accepting connection: %v", err)
   continue
  }
  go handleConnection(conn)
 }
}

func main() {
 wechatPort := 18888
 socketPort := 10808
 //间隔 5s 执行一次
 ticker := time.NewTicker(5 * time.Second)
 var err error
 go func() {
  for range ticker.C {
   wechatHTTPAPI(WeChatMsgStartHook, wechatPort, "post", map[string]interface{}{"port": socketPort})
  }
 }()
 defer ticker.Stop()
 if err != nil {
  log.Fatalf("Failed to start WeChat message hook: %v", err)
 }

 err = startSocketServer(socketPort)
 if err != nil {
  log.Fatalf("Failed to start socket server: %v", err)
 }

 // Note: In a real application, you'd want to implement proper shutdown handling
 _, _ = wechatHTTPAPI(WeChatMsgStopHook, wechatPort, "post", nil)
}