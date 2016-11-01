#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <iostream>

using namespace std;

// this is our proto of foo
#include "control_signals.pb.h"

int main(int argc, char **argv)
{
  struct sockaddr_in server;
  struct sockaddr_in dest;
  int socket_fd, client_fd;
  socklen_t size;
  int yes = 1;

  if ((socket_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
	printf("ERROR socket failure");
  if (setsockopt(socket_fd, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) < 0)
	printf("ERROR setsockopt");
  memset(&server, 0, sizeof(server));
  memset(&dest, 0, sizeof(dest));
  server.sin_family = AF_INET;
  server.sin_port = htons(10001);
  server.sin_addr.s_addr = INADDR_ANY;
  if (bind(socket_fd, (struct sockaddr *)&server, sizeof(struct sockaddr)) < 0)
	printf("ERROR binding failure");
  
  if (listen(socket_fd, 5) < 0)
	printf("ERROR listening failure");

  if ((client_fd = accept(socket_fd, (struct sockaddr *)&dest, &size)) < 0)
	printf("ERROR acception failure");
  printf("Server got connection from client\n");

  GOOGLE_PROTOBUF_VERIFY_VERSION;
  StartRequest foo;
  foo.set_port(4);
  foo.set_channels(32);

  // Receive size of message
  uint16_t rawsize;
  recv(client_fd, &rawsize, sizeof(rawsize), 0);
  printf("Received size=%d\n", rawsize);
  // Receive message
  vector<char> buffer(rawsize);
  recv(client_fd, buffer.data(), buffer.size(), 0);
  if (foo.ParseFromArray(buffer.data(), buffer.size()) == false)
	throw exception();
  printf("Received foo with port=%d and channels=%d\n", foo.port(), foo.channels());

  foo.set_port(10002);
  std::string buf;
  foo.SerializeToString(&buf);
  // Send size of message
  uint16_t sizebuf = strlen(buf.c_str());
  printf("Sending size=%d\n", sizebuf);
  sendto(client_fd, &sizebuf, sizeof(sizebuf), 0, (struct sockaddr *)&socket_fd, sizeof(server));

  // Send message
  printf("Sending foo with port=%d and channels=%d\n", foo.port(), foo.channels());
  sendto(client_fd, buf.data(), strlen(buf.c_str()), 0, (struct sockaddr *)&socket_fd, sizeof(server));
  

  close(client_fd);

  return 0;
}
