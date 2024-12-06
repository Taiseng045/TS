function deletePro(productID){
    fetch('/admin/delete',{
        method: 'POST',
        body: JSON.stringify({productID: productID}),
    }).then((_res)=>{
        window.location.href = '/admin';
    })
}