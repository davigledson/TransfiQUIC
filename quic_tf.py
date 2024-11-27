import os
import time
import asyncio
from aioquic.asyncio import connect, serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.quic.events import StreamDataReceived

#barras de progresso
import tqdm

BUFFER_SIZE = 4096 *400
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5001


class FileTransferProtocol(QuicConnectionProtocol):
    """Protocolo para o Servidor QUIC para recepção de arquivos."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_info_received = False
        self.filename = None
        self.filesize = 0
        self.received_size = 0

    def quic_event_received(self, event):
        if isinstance(event, StreamDataReceived):
            stream_id = event.stream_id
            data = event.data

            # Processar o nome do arquivo e tamanho
            if not self.file_info_received:
                self.file_info_received = True
                filename, filesize = data.decode().split("|")
                self.filename = f"received_{filename}"
                self.filesize = int(filesize)
                self.received_size = 0
                print(f"Recebendo arquivo: {self.filename} ({self.filesize} bytes)")
            else:
                # Salvar os dados do arquivo
                with open(self.filename, "ab") as f:
                    f.write(data)
                    self.received_size += len(data)
                print(f"Recebido {self.received_size}/{self.filesize} bytes")

            # Verificar se o arquivo foi completamente recebido
            if self.received_size >= self.filesize:
                print(f"Recepção do arquivo {self.filename} concluída.")


async def send_file_quic(filename):
    """Função para enviar arquivo via QUIC e medir o desempenho."""
    filesize = os.path.getsize(filename)
    print(f"Tamanho do arquivo: {filesize} bytes")

    # Configuração QUIC
    config = QuicConfiguration(is_client=True)
    config.load_verify_locations("cert.pem")  # Verificar certificado do servidor

    # Estabelecer a conexão QUIC
    async with connect(SERVER_HOST, SERVER_PORT, configuration=config) as connection:
        # Criar o ID do stream
        stream_id = connection._quic.get_next_available_stream_id()

        # Enviar informações do arquivo
        file_info = f"{os.path.basename(filename)}|{filesize}".encode()
        connection._quic.send_stream_data(stream_id, file_info)

        # Início da medição de tempo
        start_time = time.time()

        # Enviar o conteúdo do arquivo
        with open(filename, "rb") as file:
            progress = tqdm.tqdm(range(filesize), f"Enviando {filename}", unit="B", unit_scale=True, unit_divisor=1024)
            while (data := file.read(BUFFER_SIZE)):
                connection._quic.send_stream_data(stream_id, data)
                progress.update(len(data))

        # Finalizar o stream
        connection._quic.send_stream_data(stream_id, b"", end_stream=True)

        # Fim da medição
        end_time = time.time()
        transfer_time = end_time - start_time
        transfer_rate = filesize / transfer_time / (1024 * 1024)

        print(f"Envio via QUIC concluído. Tempo: {transfer_time:.2f} segundos. Taxa: {transfer_rate:.2f} MB/s")

#retorna as metricas para a comparação
    return filesize, transfer_time, transfer_rate


async def start_server():
    """Função para iniciar o servidor QUIC """
    config = QuicConfiguration(is_client=False)
    config.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
    print(f"Servidor QUIC iniciado em {SERVER_HOST}:{SERVER_PORT}. Aguardando conexões...")
    await serve(SERVER_HOST, SERVER_PORT, configuration=config, create_protocol=FileTransferProtocol)


async def main():
    print("Selecione uma opção:")
    print("1. Iniciar servidor")
    print("2. Enviar arquivo como cliente")
    choice = input("Escolha (1/2): ").strip()

    if choice == "1":
        await start_server()
    elif choice == "2":
        filename = input("Caminho do arquivo para enviar: ").strip()
        if os.path.exists(filename):
            # receber as métricas
            filesize, transfer_time, transfer_rate = await send_file_quic(filename)


            print("\nMétricas de Desempenho de Envio via QUIC:")
            print(f"Tamanho do arquivo: {filesize / (1024 * 1024):.2f} MB")
            print(f"Tempo de Envio: {transfer_time:.2f} segundos")
            print(f"Taxa de Transferência: {transfer_rate:.2f} MB/s")
        else:
            print("Arquivo não encontrado.")
    else:
        print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    asyncio.run(main())

