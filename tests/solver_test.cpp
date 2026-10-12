// SPDX-License-Identifier: LGPL-2.1-or-later
#include <GCS.h>
#include <cmath>
#include <iostream>
#include <stdexcept>
int main() {
    for(auto [width,height]:{std::pair{13.0,7.0},std::pair{0.1,0.05},std::pair{1000.0,450.0}}){
        double p[8]={.03,.04,width*.9,.08,width*1.1,height*.9,.05,height*1.1},zero=0;
        GCS::System s;GCS::VEC_pD unknown;
        for(double& v:p)unknown.push_back(&v);
        s.declareUnknowns(unknown);
        s.addConstraintEqual(&p[0],&zero,1);s.addConstraintEqual(&p[1],&zero,2);
        s.addConstraintEqual(&p[1],&p[3],3);s.addConstraintEqual(&p[2],&p[4],4);
        s.addConstraintEqual(&p[5],&p[7],5);s.addConstraintEqual(&p[6],&p[0],6);
        s.addConstraintDifference(&p[0],&p[2],&width,7);s.addConstraintDifference(&p[1],&p[7],&height,8);
        s.initSolution();auto result=s.solve();s.applySolution();
        double residual=std::max(std::abs((p[2]-p[0])-width),std::abs((p[7]-p[1])-height));
        if(result!=GCS::SolveStatus::Success||residual>1e-6)throw std::runtime_error("Solver dimensions or convergence failed");
        std::cout<<"PASS: constrained rectangle "<<width<<" x "<<height<<" mm, residual "<<residual<<'\n';
    }
}
