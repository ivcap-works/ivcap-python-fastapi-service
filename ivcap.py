
from utils import IVCAPRestService, IVCAPService
from service import title, description, Request, Response

Service = IVCAPService(
    name=title,
    description=description,
    controller=IVCAPRestService(
        request=Request,
        response=Response,
    ),
)

print(Service.model_dump_json(indent=2))