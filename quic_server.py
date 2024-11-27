import asyncio
from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio.protocol import QuicConnectionProtocol
import aioquic


class FileTransferProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_info_received = False
        self.filename = None
        self.filesize = 0
        self.received_size = 0

    async def quic_event_received(self, event):
        if isinstance(event, aioquic.quic.events.StreamDataReceived):
            if not self.file_info_received:
                # Processar nome do arquivo e tamanho
                self.file_info_received = True
                filename, filesize = event.data.decode().split("|")
                self.filename = f"received_{filename}"
                self.filesize = int(filesize)
                print(f"Recebendo arquivo: {self.filename} ({self.filesize} bytes)")
            else:
                # Salvar os dados do arquivo
                with open(self.filename, "ab") as f:
                    f.write(event.data)
                    self.received_size += len(event.data)
                print(f"Recebido {self.received_size}/{self.filesize} bytes")

            # Verificar se o arquivo foi completamente recebido
            if self.received_size >= self.filesize:
                print(f"Recepção do arquivo {self.filename} concluída.")


async def start_server():
    """Inicia o servidor QUIC."""
    config = QuicConfiguration(is_client=False)
    config.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    print(f"Servidor QUIC iniciado em 127.0.0.1:5001. Aguardando conexões...")
    await serve("127.0.0.1", 5001, configuration=config, create_protocol=FileTransferProtocol)


async def main():
    # Inicializa o servidor QUIC
    server_task = asyncio.create_task(start_server())

    try:
        # Mantém o servidor ativo até o encerramento manual (CTRL+C)
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
        server_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())


#netstat -ano | findstr :5001
#taskkill /PID 7072 /F