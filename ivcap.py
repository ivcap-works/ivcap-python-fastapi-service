
from utils import IVCAPRestService, IVCAPService
from service import title, description, Request, Response

Service = IVCAPService(
    name=title,
    description=description,
    controller=IVCAPRestService(
        request=Request,
        response=Response,
        path="/delayed",
        command=["python",  "service.py"],
        port=8080,
        readyPath="/_healtz",
    ),
)

print(Service.model_dump_json(by_alias=True, indent=2))