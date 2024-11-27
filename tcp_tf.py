import socket
import os
import tqdm
import time
#netstat -ano | findstr :5001
#taskkill /PID 12345 /F

# Configurações gerais
BUFFER_SIZE = 4096 * 300
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9999


def receive_file_tcp():
    """Função para receber arquivo via TCP."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(1)
    print(f"Servidor TCP aguardando conexões em {SERVER_HOST}:{SERVER_PORT}...")

    conn, addr = server_socket.accept()
    print(f"Conexão recebida de {addr}")

    # Recebe o nome do arquivo e o tamanho
    data = conn.recv(BUFFER_SIZE).decode()
    filename, filesize = data.split("|")
    filename = f"received_{filename}"
    filesize = int(filesize)

    print(f"Recebendo arquivo {filename} ({filesize} bytes)...")

    with open(filename, "wb") as file:
        #progress = tqdm.tqdm(range(filesize), f"Recebendo {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        #for _ in progress:
           # data = conn.recv(BUFFER_SIZE)
           # if not data:
              #  break

            #progress.update(len(data))
        file.write(data)
    print(f"Arquivo {filename} recebido com sucesso.")
    conn.close()
    server_socket.close()


def send_file_tcp(filename):
    """Função para enviar arquivo via TCP e medir o desempenho."""
    filesize = os.path.getsize(filename)
    print(f"Tamanho do arquivo: {filesize} bytes")

    # Criando socket TCP para o cliente
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))

    # Envia informações do arquivo (nome e tamanho)
    client_socket.send(f"{os.path.basename(filename)}|{filesize}".encode())

    # Início da medição de tempo de envio
    start_time = time.time()

    # Envia o conteúdo do arquivo
    with open(filename, "rb") as file:
        progress = tqdm.tqdm(range(filesize), f"Enviando {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        for _ in progress:
            data = file.read(BUFFER_SIZE)
            if not data:
                break
            client_socket.send(data)
            progress.update(len(data))

    # Final da medição de tempo de envio
    end_time = time.time()
    transfer_time = end_time - start_time  # Tempo de envio em segundos
    transfer_rate = filesize / transfer_time / (1024 * 1024)  # Taxa de transferência em MB/s

    client_socket.close()
    print(f"Envio via TCP concluído. Tempo: {transfer_time:.2f} segundos. Taxa: {transfer_rate:.2f} MB/s")

    return filesize, transfer_time, transfer_rate


# Função principal
def main():
    print("Selecione uma opção:")
    print("1. Enviar arquivo")
    print("2. Receber arquivo")
    choice = input("Escolha (1 ou 2): ").strip()

    if choice == "1":
        filename = input("Caminho do arquivo para enviar: ").strip()
        if os.path.exists(filename):
            # Enviar arquivo e medir as métricas
            filesize, transfer_time, transfer_rate = send_file_tcp(filename)

            # Exibir as métricas de envio
            print("\nMétricas de Desempenho de Envio via TCP:")
            print(f"Tamanho do arquivo: {filesize / (1024 * 1024):.2f} MB")
            print(f"Tempo de Envio: {transfer_time:.2f} segundos")
            print(f"Taxa de Transferência: {transfer_rate:.2f} MB/s")
        else:
            print("Arquivo não encontrado.")
    elif choice == "2":
        receive_file_tcp()
    else:
        print("Opção inválida.")

if __name__ == "__main__":
    main()

    # files_to_send/arq.jpg