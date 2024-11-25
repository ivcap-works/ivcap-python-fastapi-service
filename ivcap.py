
from utils import IVCAPRestService, IVCAPService
from service import title, description, Request, Response

Service = IVCAPService(
    name=title,
    description=description,
    controller=IVCAPRestService(
        request=Request,
        response=Response,
        command=["./run.sh"],
        port=8080,
        readyPath="/_healtz",
    ),
)

print(Service.model_dump_json(by_alias=True, indent=2))