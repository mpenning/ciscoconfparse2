use log::info;
use moe_logger::LogConfig;
use rexpect::spawn;
use rexpect::error::*;

fn copy_and_extract_tarball() -> Result<(), Error> {
    //colog::init();
    let log_config = LogConfig::builder()
        .env("MOE_LOG_LEVEL")
        .output("deploy_docs.log")
        .format("{t} {L} {T} > {M}\n")
        .rotation(10000)
        .finish();
    moe_logger::init(log_config);

    info!("Starting file copy to chestnut");
    let mut sess = spawn("scp /home/mpenning/ccp2.tar.gz chestnut.he.net:", Some(45_000))?;
    sess.exp_eof()?;
    info!("  Finished file copy to chestnut");

    info!("Starting tarball extraction");
    let mut sess = spawn("ssh chestnut.he.net", Some(5_000))?;
    sess.exp_regex("\\$")?;
    sess.send_line("cd public_html/py/ciscoconfparse2")?;
    sess.exp_regex("\\$")?;
    sess.send_line("rm -rf *")?;
    sess.exp_regex("\\$")?;
    sess.send_line("cp ~/ccp2.tar.gz .")?;
    sess.exp_regex("\\$")?;
    sess.send_line("tar xvfz ccp2.tar.gz")?;
    sess.exp_regex("\\$")?;
    sess.send_line("exit")?;
    sess.exp_eof()?;
    info!("  Finished tarball extraction");

    Ok(())

}

fn main() {
    copy_and_extract_tarball().unwrap_or_else(|e| panic!("doc deploy job failed with {}", e));
}
