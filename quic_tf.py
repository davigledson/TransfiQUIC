import os
import time
import asyncio
from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived
import tqdm

BUFFER_SIZE = 4096
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5001


async def send_file_quic(filename):
    """Função para enviar arquivo via QUIC e medir o desempenho."""
    filesize = os.path.getsize(filename)
    print(f"Tamanho do arquivo: {filesize} bytes")

    # Configuração QUIC
    config = QuicConfiguration(is_client=True)
    config.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    # Estabelece a conexão QUIC
    connection = await connect((SERVER_HOST, SERVER_PORT), configuration=config)

    # Envia o nome do arquivo e o tamanho
    stream = connection.quic.create_stream()
    stream.send(f"{os.path.basename(filename)}|{filesize}".encode())

    # Início da medição de tempo de envio
    start_time = time.time()

    # Envia o conteúdo do arquivo
    with open(filename, "rb") as file:
        progress = tqdm.tqdm(range(filesize), f"Enviando {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        while (data := file.read(BUFFER_SIZE)):
            stream.send(data)
            progress.update(len(data))

    # Final da medição de tempo de envio
    end_time = time.time()
    transfer_time = end_time - start_time  # Tempo de envio em segundos
    transfer_rate = filesize / transfer_time / (1024 * 1024)  # Taxa de transferência em MB/s

    print(f"Envio via QUIC concluído. Tempo: {transfer_time:.2f} segundos. Taxa: {transfer_rate:.2f} MB/s")
    connection.close()

    return filesize, transfer_time, transfer_rate


async def main():
    filename = input("Caminho do arquivo para enviar: ").strip()
    if os.path.exists(filename):
        # Enviar arquivo e medir as métricas
        filesize, transfer_time, transfer_rate = await send_file_quic(filename)

        # Exibir as métricas de envio
        print("\nMétricas de Desempenho de Envio via QUIC:")
        print(f"Tamanho do arquivo: {filesize / (1024 * 1024):.2f} MB")
        print(f"Tempo de Envio: {transfer_time:.2f} segundos")
        print(f"Taxa de Transferência: {transfer_rate:.2f} MB/s")
    else:
        print("Arquivo não encontrado.")


if __name__ == "__main__":
    asyncio.run(main())

